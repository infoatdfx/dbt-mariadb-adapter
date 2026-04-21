"""MariaDB 11.x-specific functional tests.

These cover behaviour that's not in the standard dbt-tests-adapter suite
but matters for the 11.x feature set: JSON columns, fractional-second
timestamps, SEQUENCE objects, larger incremental merges, and the
information_schema shape dbt's catalog depends on.

Each test is self-contained — it declares its own models via dbt's
project fixture. They run against whichever MariaDB is configured via
DBT_MARIADB_PORT (see tests/conftest.py).
"""
from __future__ import annotations

import pytest

from dbt.tests.util import run_dbt


# ---------------------------------------------------------------------------
# JSON columns (MariaDB 10.2+, full function coverage in 11.x)
# ---------------------------------------------------------------------------

json_model_sql = """
{{ config(materialized='table') }}
select
    1 as id,
    cast('{"name": "alice", "tags": ["a", "b"]}' as json) as payload
union all
select
    2 as id,
    cast('{"name": "bob",   "tags": ["c"]}' as json) as payload
"""


class TestJSONColumn:
    @pytest.fixture(scope="class")
    def models(self):
        return {"json_model.sql": json_model_sql}

    def test_json_model_builds_and_queries(self, project):
        results = run_dbt(["run"])
        assert len(results) == 1

        with project.adapter.connection_named("_test"):
            _, table = project.adapter.execute(
                f"""
                select
                    json_extract(payload, '$.name') as name,
                    json_length(json_extract(payload, '$.tags')) as n_tags
                from {project.test_schema}.json_model
                order by id
                """,
                fetch=True,
            )
        rows = [(str(r[0]), r[1]) for r in table.rows]
        # MariaDB returns JSON strings with quotes around string scalars
        assert rows[0][0] in ('"alice"', "alice")
        assert rows[0][1] == 2
        assert rows[1][1] == 1


# ---------------------------------------------------------------------------
# Timestamp fractional seconds (DATETIME(6))
# ---------------------------------------------------------------------------

fractional_timestamp_model_sql = """
{{ config(materialized='table') }}
select cast('2025-01-01 12:34:56.123456' as datetime(6)) as t
"""


class TestFractionalTimestamp:
    @pytest.fixture(scope="class")
    def models(self):
        return {"frac_ts.sql": fractional_timestamp_model_sql}

    def test_fractional_timestamp_preserved(self, project):
        run_dbt(["run"])

        with project.adapter.connection_named("_test"):
            _, table = project.adapter.execute(
                f"select microsecond(t) from {project.test_schema}.frac_ts",
                fetch=True,
            )
        assert table.rows[0][0] == 123456


# ---------------------------------------------------------------------------
# SEQUENCE (MariaDB-only SQL object)
# ---------------------------------------------------------------------------

class TestMariaDBSequence:
    def test_sequence_can_be_created_and_read(self, project):
        with project.adapter.connection_named("_test"):
            project.adapter.execute(
                f"create sequence if not exists {project.test_schema}.dbt_test_seq "
                "start with 1 increment by 1"
            )
            _, table = project.adapter.execute(
                f"select nextval({project.test_schema}.dbt_test_seq)",
                fetch=True,
            )
            project.adapter.execute(
                f"drop sequence if exists {project.test_schema}.dbt_test_seq"
            )
        assert table.rows[0][0] == 1


# ---------------------------------------------------------------------------
# Larger incremental merge — stress test the unique-key flow at 10k+ rows
# ---------------------------------------------------------------------------

large_incremental_model_sql = """
{{
  config(
    materialized='incremental',
    unique_key='id',
    on_schema_change='append_new_columns'
  )
}}
with seq as (
  select seq as id, concat('name_', seq) as name
  from seq_1_to_12000
)
select * from seq
{% if is_incremental() %}
where id > (select coalesce(max(id), 0) from {{ this }})
{% endif %}
"""


class TestLargeIncrementalMerge:
    @pytest.fixture(scope="class")
    def models(self):
        return {"large_inc.sql": large_incremental_model_sql}

    def test_incremental_merge_handles_many_rows(self, project):
        # First run populates.
        run_dbt(["run"])
        # Second run should merge on unique_key without errors.
        run_dbt(["run"])

        with project.adapter.connection_named("_test"):
            _, table = project.adapter.execute(
                f"select count(*) from {project.test_schema}.large_inc",
                fetch=True,
            )
        assert table.rows[0][0] == 12000


# ---------------------------------------------------------------------------
# information_schema.COLUMNS shape
# ---------------------------------------------------------------------------

_info_schema_model_sql = """
{{ config(materialized='table') }}
select
    cast(1 as integer) as id,
    cast('hello' as varchar(32)) as label,
    cast('2025-01-01' as date) as d
"""


class TestInformationSchemaColumnsShape:
    @pytest.fixture(scope="class")
    def models(self):
        return {"info_schema_model.sql": _info_schema_model_sql}

    def test_information_schema_exposes_expected_metadata(self, project):
        run_dbt(["run"])

        with project.adapter.connection_named("_test"):
            _, table = project.adapter.execute(
                f"""
                select column_name, data_type
                from information_schema.columns
                where table_schema = '{project.test_schema}'
                  and table_name = 'info_schema_model'
                order by ordinal_position
                """,
                fetch=True,
            )
        rows = [(r[0], r[1]) for r in table.rows]
        names = [r[0] for r in rows]
        assert names == ["id", "label", "d"]
        types = {r[0]: r[1] for r in rows}
        assert types["id"] == "int"
        assert types["label"] in {"varchar", "character varying"}
        assert types["d"] == "date"


# ---------------------------------------------------------------------------
# Schema lifecycle with existing data
# ---------------------------------------------------------------------------

class TestSchemaLifecycle:
    def test_drop_schema_cascades_tables(self, project):
        schema = f"{project.test_schema}_life"
        adapter = project.adapter

        with adapter.connection_named("_test"):
            adapter.execute(f"create schema if not exists {schema}")
            adapter.execute(f"create table {schema}.tmp (id int)")
            adapter.execute(f"insert into {schema}.tmp values (1), (2)")
            adapter.execute(f"drop schema if exists {schema}")

            _, table = adapter.execute(
                f"select count(*) from information_schema.schemata "
                f"where schema_name = '{schema}'",
                fetch=True,
            )
        assert table.rows[0][0] == 0


