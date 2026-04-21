from unittest import mock

import pytest

from dbt_common.contracts.constraints import ConstraintType
from dbt_common.exceptions import DbtRuntimeError

from dbt.adapters.base.impl import ConstraintSupport
from dbt.adapters.mariadb.impl import MariaDBAdapter


def _adapter():
    """Build a MariaDBAdapter without going through __init__ (which needs a
    full RuntimeConfig). This is the standard trick used in adapter unit
    tests — we exercise classmethods / pure functions only."""
    return MariaDBAdapter.__new__(MariaDBAdapter)


def test_date_function_returns_current_date():
    assert MariaDBAdapter.date_function() == "current_date()"


def test_convert_datetime_type_returns_timestamp():
    assert MariaDBAdapter.convert_datetime_type(None, 0) == "timestamp"


def test_quote_wraps_with_backticks():
    assert MariaDBAdapter.quote("my_col") == "`my_col`"


def test_constraint_support_matrix():
    support = MariaDBAdapter.CONSTRAINT_SUPPORT
    assert support[ConstraintType.check] == ConstraintSupport.ENFORCED
    assert support[ConstraintType.not_null] == ConstraintSupport.ENFORCED
    assert support[ConstraintType.unique] == ConstraintSupport.ENFORCED
    assert support[ConstraintType.primary_key] == ConstraintSupport.ENFORCED
    # Foreign keys cannot be expressed in CREATE TABLE AS SELECT
    assert support[ConstraintType.foreign_key] == ConstraintSupport.NOT_SUPPORTED


def test_capabilities_declared():
    from dbt.adapters.capability import Capability, Support

    caps = MariaDBAdapter._capabilities
    assert caps[Capability.SchemaMetadataByRelations].support == Support.Full
    assert caps[Capability.TableLastModifiedMetadata].support == Support.Full
    assert caps[Capability.MicrobatchConcurrency].support == Support.Full


def test_catalog_by_relation_support_enabled():
    assert MariaDBAdapter.CATALOG_BY_RELATION_SUPPORT is True


def test_valid_incremental_strategies():
    adapter = _adapter()
    strategies = adapter.valid_incremental_strategies()
    assert set(strategies) == {"append", "delete+insert", "merge", "microbatch"}


def test_valid_snapshot_strategies():
    strategies = MariaDBAdapter.valid_snapshot_strategies()
    assert "timestamp" in strategies
    assert "check" in strategies


def test_timestamp_add_sql_default():
    adapter = _adapter()
    sql = adapter.timestamp_add_sql("now()")
    assert sql == "date_add(now(), interval 1 hour)"


def test_timestamp_add_sql_custom_interval():
    adapter = _adapter()
    sql = adapter.timestamp_add_sql("now()", number=7, interval="day")
    assert sql == "date_add(now(), interval 7 day)"


def test_string_add_sql_append():
    adapter = _adapter()
    assert adapter.string_add_sql("name", "_v2") == "concat(name, '_v2')"


def test_string_add_sql_prepend():
    adapter = _adapter()
    assert adapter.string_add_sql("name", "v2_", location="prepend") == "concat(v2_, 'name')"


def test_string_add_sql_invalid_location_raises():
    adapter = _adapter()
    with pytest.raises(DbtRuntimeError, match="unexpected location value"):
        adapter.string_add_sql("x", "y", location="middle")


def test_update_column_sql_without_where():
    adapter = _adapter()
    sql = adapter.update_column_sql("target", "col", "source.col")
    assert sql == "update target set col = source.col"


def test_update_column_sql_with_where():
    adapter = _adapter()
    sql = adapter.update_column_sql("target", "col", "source.col", where_clause="id = 1")
    assert sql == "update target set col = source.col where id = 1"


def test_list_relations_returns_empty_on_not_found_error():
    adapter = _adapter()
    schema_rel = mock.MagicMock()
    schema_rel.__str__ = lambda self: "mydb"
    err = DbtRuntimeError("MariaDB database 'mydb' not found")
    err.msg = "MariaDB database 'mydb' not found"

    with mock.patch.object(MariaDBAdapter, "execute_macro", side_effect=err):
        result = adapter.list_relations_without_caching(schema_rel)
    assert result == []


def test_list_relations_returns_empty_on_generic_error():
    adapter = _adapter()
    schema_rel = mock.MagicMock()
    err = DbtRuntimeError("some other error")
    err.msg = "some other error"

    with mock.patch.object(MariaDBAdapter, "execute_macro", side_effect=err):
        result = adapter.list_relations_without_caching(schema_rel)
    assert result == []


def test_list_relations_parses_rows():
    adapter = _adapter()
    schema_rel = mock.MagicMock()
    rows = [
        (None, "t1", "analytics", "table"),
        (None, "v1", "analytics", "view"),
    ]
    with mock.patch.object(MariaDBAdapter, "execute_macro", return_value=rows):
        result = adapter.list_relations_without_caching(schema_rel)

    assert len(result) == 2
    assert {r.identifier for r in result} == {"t1", "v1"}
    assert {r.schema for r in result} == {"analytics"}


def test_list_relations_rejects_malformed_row():
    adapter = _adapter()
    schema_rel = mock.MagicMock()
    rows = [("only", "three", "columns")]
    with mock.patch.object(MariaDBAdapter, "execute_macro", return_value=rows):
        with pytest.raises(DbtRuntimeError, match="got 3 values, expected 4"):
            adapter.list_relations_without_caching(schema_rel)
