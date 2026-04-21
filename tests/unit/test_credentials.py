import pytest

from dbt_common.exceptions import DbtRuntimeError

from dbt.adapters.mariadb.connections import (
    DEFAULT_APPLICATION_NAME,
    MariaDBCredentials,
)


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
    # database is normalised to None by __post_init__
    assert creds.database is None


def test_database_equals_schema_is_allowed():
    creds = MariaDBCredentials(
        server="localhost",
        schema="analytics",
        database="analytics",
        username="u",
        password="p",
    )
    # The invariant (database == schema) passed; still normalised to None.
    assert creds.database is None


def test_construct_raises_when_database_conflicts_with_schema():
    with pytest.raises(DbtRuntimeError, match="database must be omitted"):
        MariaDBCredentials(
            server="localhost",
            schema="analytics",
            database="other",
            username="u",
            password="p",
        )


def test_post_init_raises_when_database_mutated_after_construction():
    # Defensive: if something deserialises creds with a bad database (e.g.
    # from a stale cache) and re-runs __post_init__, we still catch it.
    creds = MariaDBCredentials(
        server="localhost", schema="analytics", username="u", password="p"
    )
    creds.database = "other"
    with pytest.raises(DbtRuntimeError, match="database must be omitted"):
        creds.__post_init__()


def test_connection_keys_include_new_fields(minimal_credentials):
    keys = minimal_credentials._connection_keys()
    assert {
        "server",
        "unix_socket",
        "port",
        "database",
        "schema",
        "user",
        "connect_timeout",
        "retries",
        "application_name",
    } == set(keys)


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


def test_defaults_for_new_fields():
    creds = MariaDBCredentials(
        server="localhost", schema="analytics", username="u", password="p"
    )
    assert creds.connect_timeout == 10
    assert creds.retries == 1
    assert creds.application_name == DEFAULT_APPLICATION_NAME


def test_retries_and_timeout_overridable():
    creds = MariaDBCredentials(
        server="localhost",
        schema="analytics",
        username="u",
        password="p",
        connect_timeout=30,
        retries=4,
        application_name="dbt-run-nightly",
    )
    assert creds.connect_timeout == 30
    assert creds.retries == 4
    assert creds.application_name == "dbt-run-nightly"
