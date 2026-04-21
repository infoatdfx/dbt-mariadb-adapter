import pytest

from dbt_common.exceptions import DbtRuntimeError

from dbt.adapters.mariadb.connections import MariaDBCredentials


def test_type_is_mariadb(minimal_credentials):
    assert minimal_credentials.type == "mariadb"


def test_unique_field_returns_schema(minimal_credentials):
    assert minimal_credentials.unique_field == "analytics"


def test_minimal_credentials_parse(minimal_credentials_kwargs):
    creds = MariaDBCredentials(**minimal_credentials_kwargs)
    assert creds.server == "localhost"
    assert creds.schema == "analytics"
    assert creds.username == "dbt"
    assert creds.password == "secret"
    # database is force-cleared by __init__
    assert creds.database is None


def test_database_equals_schema_is_allowed():
    # database == schema is a no-op, should not raise
    creds = MariaDBCredentials(
        server="localhost",
        schema="analytics",
        database="analytics",
        username="u",
        password="p",
    )
    assert creds.database is None  # still cleared by __init__


def test_post_init_raises_when_database_conflicts_with_schema():
    # __init__ force-clears `database`, so simulate a stale/manually-set value
    # reaching __post_init__ (e.g. via deserialization).
    creds = MariaDBCredentials(
        server="localhost", schema="analytics", username="u", password="p"
    )
    creds.database = "other"
    with pytest.raises(DbtRuntimeError, match="database must be omitted"):
        creds.__post_init__()


def test_post_init_noop_when_database_matches_schema():
    creds = MariaDBCredentials(
        server="localhost", schema="analytics", username="u", password="p"
    )
    creds.database = "analytics"
    # Should not raise
    creds.__post_init__()


def test_connection_keys_expected_fields(minimal_credentials):
    keys = minimal_credentials._connection_keys()
    assert set(keys) == {"server", "unix_socket", "port", "database", "schema", "user"}


@pytest.mark.parametrize(
    "alias, attr",
    [
        ("UID", "username"),
        ("user", "username"),
        ("PWD", "password"),
        ("host", "server"),
    ],
)
def test_credential_aliases(alias, attr):
    assert MariaDBCredentials._ALIASES[alias] == attr


def test_full_credentials_retain_all_fields(full_credentials):
    assert full_credentials.port == 3307
    assert full_credentials.charset == "utf8mb4"
    assert full_credentials.collation == "utf8mb4_uca1400_ai_ci"
    assert full_credentials.ssl_disabled is True


def test_unix_socket_supported():
    creds = MariaDBCredentials(
        unix_socket="/var/run/mysqld/mysqld.sock",
        schema="analytics",
        username="u",
        password="p",
    )
    assert creds.unix_socket == "/var/run/mysqld/mysqld.sock"
    assert creds.server == ""
