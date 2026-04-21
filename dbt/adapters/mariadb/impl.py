from concurrent.futures import Future
from dataclasses import asdict
from typing import Any, Dict, FrozenSet, Iterable, List, Optional, Tuple

import agate

from dbt.adapters.base import BaseRelation
from dbt.adapters.base.impl import ConstraintSupport, catch_as_completed
from dbt.adapters.capability import (
    Capability,
    CapabilityDict,
    CapabilitySupport,
    Support,
)
from dbt.adapters.events.logging import AdapterLogger
from dbt.adapters.mariadb import (
    MariaDBColumn,
    MariaDBConnectionManager,
    MariaDBRelation,
)
from dbt.adapters.sql import SQLAdapter
from dbt_common.clients.agate_helper import DEFAULT_TYPE_TESTER
from dbt_common.contracts.constraints import ConstraintType
from dbt_common.exceptions import CompilationError, DbtRuntimeError
from dbt_common.utils.executor import executor

logger = AdapterLogger("mariadb")

LIST_SCHEMAS_MACRO_NAME = "list_schemas"
LIST_RELATIONS_MACRO_NAME = "list_relations_without_caching"


class MariaDBAdapter(SQLAdapter):
    Relation = MariaDBRelation
    Column = MariaDBColumn
    ConnectionManager = MariaDBConnectionManager

    CONSTRAINT_SUPPORT = {
        ConstraintType.check: ConstraintSupport.ENFORCED,
        ConstraintType.not_null: ConstraintSupport.ENFORCED,
        ConstraintType.unique: ConstraintSupport.ENFORCED,
        ConstraintType.primary_key: ConstraintSupport.ENFORCED,
        # Foreign keys are supported but not in CREATE TABLE AS SELECT, which is
        # what dbt uses. Users can still add them via a post-hook.
        ConstraintType.foreign_key: ConstraintSupport.NOT_SUPPORTED,
    }

    # dbt-core checks these to decide whether to use fast-path metadata APIs
    # and to render the right warnings. Mirror the dbt-postgres declaration
    # where it makes sense; MariaDB has no materialized views so we say so
    # explicitly instead of leaving the capability undeclared.
    _capabilities: CapabilityDict = CapabilityDict(
        {
            Capability.SchemaMetadataByRelations: CapabilitySupport(
                support=Support.Full
            ),
            Capability.TableLastModifiedMetadata: CapabilitySupport(
                support=Support.Full
            ),
            Capability.MicrobatchConcurrency: CapabilitySupport(
                support=Support.NotImplemented
            ),
        }
    )

    # Allow dbt-core to batch catalog lookups via `get_catalog_by_relations`.
    CATALOG_BY_RELATION_SUPPORT: bool = True

    @classmethod
    def date_function(cls):
        return "current_date()"

    @classmethod
    def convert_datetime_type(cls, agate_table: agate.Table, col_idx: int) -> str:
        return "timestamp"

    @classmethod
    def quote(cls, identifier: str) -> str:
        return "`{}`".format(identifier)

    def valid_incremental_strategies(self) -> List[str]:
        """Incremental strategies this adapter supports out of the box.

        - `append`: plain INSERT … SELECT (no unique_key dedup)
        - `delete+insert`: DELETE … WHERE unique_key IN (new) then INSERT
        - `merge`: native MERGE is not available on MariaDB; we emulate via
          INSERT … ON DUPLICATE KEY UPDATE, which requires a primary/unique key.

        `microbatch` is intentionally absent — see the explicit rejection in
        the materialization macros.
        """
        return ["append", "delete+insert", "merge"]

    @staticmethod
    def valid_snapshot_strategies() -> FrozenSet[str]:
        return frozenset(["timestamp", "check"])

    def list_relations_without_caching(  # type: ignore[override]
        self, schema_relation: MariaDBRelation  # type: ignore[override]
    ) -> List[MariaDBRelation]:
        kwargs = {"schema_relation": schema_relation}
        try:
            results = self.execute_macro(LIST_RELATIONS_MACRO_NAME, kwargs=kwargs)
        except DbtRuntimeError as e:
            errmsg = getattr(e, "msg", "")
            if f"MariaDB database '{schema_relation}' not found" in errmsg:
                return []
            else:
                description = "Error while retrieving information about"
                logger.debug(f"{description} {schema_relation}: {e.msg}")
                return []

        relations = []
        for row in results:
            if len(row) != 4:
                raise DbtRuntimeError(
                    "Invalid value from "
                    f'"mariadb__list_relations_without_caching({kwargs})", '
                    f"got {len(row)} values, expected 4"
                )
            _, name, _schema, relation_type = row
            relation = self.Relation.create(
                schema=_schema, identifier=name, type=relation_type
            )
            relations.append(relation)

        return relations

    def get_columns_in_relation(self, relation: MariaDBRelation) -> List[MariaDBColumn]:
        rows: List[agate.Row] = super().get_columns_in_relation(relation)
        return self.parse_show_columns(relation, rows)

    def _get_columns_for_catalog(
        self, relation: MariaDBRelation
    ) -> Iterable[Dict[str, Any]]:
        columns = self.get_columns_in_relation(relation)

        for column in columns:
            as_dict = asdict(column)
            as_dict["column_name"] = as_dict.pop("column", None)
            as_dict["column_type"] = as_dict.pop("dtype")
            as_dict["table_database"] = None
            yield as_dict

    def get_relation(
        self, database: Optional[str], schema: str, identifier: str
    ) -> Optional[BaseRelation]:
        if not self.Relation.get_default_include_policy().database:
            database = None

        return super().get_relation(database, schema, identifier)

    def parse_show_columns(
        self, relation: MariaDBRelation, raw_rows: List[agate.Row]
    ) -> List[MariaDBColumn]:
        return [
            MariaDBColumn(
                table_database=None,
                table_schema=relation.schema,
                table_name=relation.name,
                table_type=relation.type,
                table_owner=None,
                table_stats=None,
                column=column.column,
                column_index=idx,
                dtype=column.dtype,
            )
            for idx, column in enumerate(raw_rows)
        ]

    def get_catalog(self, manifest) -> Tuple[agate.Table, List[Exception]]:
        schema_map = self._get_catalog_schemas(manifest)

        if len(schema_map) > 1:
            raise CompilationError(
                f"Expected only one database in get_catalog, found {list(schema_map)}"
            )

        with executor(self.config) as tpe:
            futures: List[Future[agate.Table]] = []
            for info, schemas in schema_map.items():
                for schema in schemas:
                    futures.append(
                        tpe.submit_connected(
                            self,
                            schema,
                            self._get_one_catalog,
                            info,
                            [schema],
                            manifest,
                        )
                    )
            catalogs, exceptions = catch_as_completed(futures)
        return catalogs, exceptions

    def _get_one_catalog(
        self,
        information_schema,
        schemas,
        manifest,
    ) -> agate.Table:
        if len(schemas) != 1:
            raise CompilationError(
                f"Expected only one schema in mariadb _get_one_catalog, found {schemas}"
            )

        database = information_schema.database
        schema = list(schemas)[0]

        columns: List[Dict[str, Any]] = []
        for relation in self.list_relations(database, schema):
            logger.debug("Getting table schema for relation {}", str(relation))
            columns.extend(self._get_columns_for_catalog(relation))  # type: ignore[arg-type]
        return agate.Table.from_object(columns, column_types=DEFAULT_TYPE_TESTER)

    def check_schema_exists(self, database, schema):
        results = self.execute_macro(
            LIST_SCHEMAS_MACRO_NAME, kwargs={"database": database}
        )

        return schema in [row[0] for row in results]

    # Methods used in adapter tests
    def update_column_sql(
        self,
        dst_name: str,
        dst_column: str,
        clause: str,
        where_clause: Optional[str] = None,
    ) -> str:
        clause = f"update {dst_name} set {dst_column} = {clause}"
        if where_clause is not None:
            clause += f" where {where_clause}"
        return clause

    def timestamp_add_sql(
        self, add_to: str, number: int = 1, interval: str = "hour"
    ) -> str:
        return f"date_add({add_to}, interval {number} {interval})"

    def string_add_sql(
        self,
        add_to: str,
        value: str,
        location: str = "append",
    ) -> str:
        if location == "append":
            return f"concat({add_to}, '{value}')"
        elif location == "prepend":
            return f"concat({value}, '{add_to}')"
        else:
            raise DbtRuntimeError(
                f'Got an unexpected location value of "{location}"'
            )

    def get_rows_different_sql(
        self,
        relation_a: MariaDBRelation,  # type: ignore[override]
        relation_b: MariaDBRelation,  # type: ignore[override]
        column_names: Optional[List[str]] = None,
        except_operator: str = "",  # Required to match BaseRelation.get_rows_different_sql()
    ) -> str:
        names: List[str]
        if column_names is None:
            columns = self.get_columns_in_relation(relation_a)
            names = sorted((self.quote(c.name) for c in columns))
        else:
            names = sorted((self.quote(n) for n in column_names))

        alias_a = "A"
        alias_b = "B"
        columns_csv_a = ", ".join([f"{alias_a}.{name}" for name in names])
        columns_csv_b = ", ".join([f"{alias_b}.{name}" for name in names])
        join_condition = " AND ".join(
            [f"{alias_a}.{name} = {alias_b}.{name}" for name in names]
        )
        first_column = names[0]

        # MariaDB has no EXCEPT / MINUS; emulate via left-outer join symmetric difference.
        COLUMNS_EQUAL_SQL = """
        SELECT
            row_count_diff.difference as row_count_difference,
            diff_count.num_missing as num_mismatched
        FROM (
            SELECT
                1 as id,
                table_a.num_rows - table_b.num_rows as difference
            FROM
                (SELECT COUNT(*) as num_rows FROM {relation_a}) as table_a,
                (SELECT COUNT(*) as num_rows FROM {relation_b}) as table_b
            ) as row_count_diff
        INNER JOIN (
            SELECT
                1 as id,
                COUNT(*) as num_missing FROM (

                    SELECT
                        {columns_a}
                    FROM {relation_a} as {alias_a}
                    LEFT OUTER JOIN {relation_b} as {alias_b}
                        ON {join_condition}
                    WHERE {alias_b}.{first_column} is null

                    UNION ALL

                    SELECT
                        {columns_b}
                    FROM {relation_b} as {alias_b}
                    LEFT OUTER JOIN {relation_a} as {alias_a}
                        ON {join_condition}
                    WHERE {alias_a}.{first_column} is null

                ) as missing
            ) as diff_count ON row_count_diff.id = diff_count.id
        """.strip()

        return COLUMNS_EQUAL_SQL.format(
            alias_a=alias_a,
            alias_b=alias_b,
            first_column=first_column,
            columns_a=columns_csv_a,
            columns_b=columns_csv_b,
            join_condition=join_condition,
            relation_a=str(relation_a),
            relation_b=str(relation_b),
        )
