from dbt.adapters.mariadb.column import MariaDBColumn


def test_quoted_uses_backticks():
    col = MariaDBColumn(column="my_col", dtype="INTEGER")
    assert col.quoted == "`my_col`"


def test_repr_includes_name_and_data_type():
    col = MariaDBColumn(column="my_col", dtype="INTEGER")
    rendered = repr(col)
    assert "MariaDBColumn" in rendered
    assert "my_col" in rendered
    assert "INTEGER" in rendered


def test_type_labels_mapping():
    # Driver-reported type names -> dbt-friendly labels
    assert MariaDBColumn.TYPE_LABELS["STRING"] == "TEXT"
    assert MariaDBColumn.TYPE_LABELS["VAR_STRING"] == "TEXT"
    assert MariaDBColumn.TYPE_LABELS["LONG"] == "INTEGER"
    assert MariaDBColumn.TYPE_LABELS["LONGLONG"] == "INTEGER"
    assert MariaDBColumn.TYPE_LABELS["INT"] == "INTEGER"
    assert MariaDBColumn.TYPE_LABELS["TIMESTAMP"] == "DATETIME"


def test_optional_catalog_fields_default_none():
    col = MariaDBColumn(column="x", dtype="INTEGER")
    assert col.table_database is None
    assert col.table_schema is None
    assert col.table_name is None
    assert col.table_type is None
    assert col.table_owner is None
    assert col.table_stats is None
    assert col.column_index is None
