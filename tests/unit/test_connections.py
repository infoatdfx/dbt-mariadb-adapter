from types import SimpleNamespace
from unittest import mock

import pytest

from dbt_common.exceptions import DbtDatabaseError, DbtRuntimeError

from dbt.adapters.mariadb.connections import (
    MariaDBConnectionManager,
    MariaDBCredentials,
)


def _make_connection(credentials: MariaDBCredentials, state: str = "init"):
    return SimpleNamespace(
        state=state,
        handle=None,
        credentials=credentials,
    )


def test_build_connect_kwargs_minimal(minimal_credentials):
    kwargs = MariaDBConnectionManager._build_connect_kwargs(minimal_credentials)
    assert kwargs["user"] == "dbt"
    assert kwargs["passwd"] == "secret"
    assert kwargs["host"] == "localhost"
    assert kwargs["buffered"] is True
    assert kwargs["connection_timeout"] == 10
    # Default application_name is set via init_command
    assert "init_command" in kwargs
    assert "program_name" in kwargs["init_command"]
    # Optional knobs are absent when unset
    assert "port" not in kwargs
    assert "charset" not in kwargs
    assert "collation" not in kwargs
    assert "ssl_disabled" not in kwargs
    assert "database" not in kwargs


def test_build_connect_kwargs_includes_all_optionals(full_credentials):
    kwargs = MariaDBConnectionManager._build_connect_kwargs(full_credentials)
    assert kwargs["port"] == 3307
    assert kwargs["charset"] == "utf8mb4"
    assert kwargs["collation"] == "utf8mb4_uca1400_ai_ci"
    assert kwargs["ssl_disabled"] is True


def test_build_connect_kwargs_application_name_is_escaped():
    creds = MariaDBCredentials(
        server="localhost",
        schema="analytics",
        username="u",
        password="p",
        application_name="bobby's run",
    )
    kwargs = MariaDBConnectionManager._build_connect_kwargs(creds)
    assert "bobby''s run" in kwargs["init_command"]
    assert "bobby's run" not in kwargs["init_command"]


def test_build_connect_kwargs_prefers_unix_socket_when_no_server():
    creds = MariaDBCredentials(
        unix_socket="/var/run/mysqld/mysqld.sock",
        schema="analytics",
        username="u",
        password="p",
    )
    creds.server = ""
    kwargs = MariaDBConnectionManager._build_connect_kwargs(creds)
    assert kwargs["unix_socket"] == "/var/run/mysqld/mysqld.sock"
    assert "host" not in kwargs


def test_open_success_on_first_try(minimal_credentials, mock_mysql_connector):
    mock_mysql_connector.connect.return_value = mock.MagicMock(name="driver-connection")

    conn = _make_connection(minimal_credentials)
    MariaDBConnectionManager.open(conn)

    # Only one connect call because first-try (no database) succeeded.
    mock_mysql_connector.connect.assert_called_once()
    assert conn.state == "open"


def test_open_idempotent_on_already_open_connection(
    minimal_credentials, mock_mysql_connector
):
    conn = _make_connection(minimal_credentials, state="open")
    result = MariaDBConnectionManager.open(conn)
    mock_mysql_connector.connect.assert_not_called()
    assert result is conn


def test_open_retries_with_database_on_first_failure(
    minimal_credentials, mock_mysql_connector
):
    driver_error = type("DriverError", (Exception,), {})
    mock_mysql_connector.Error = driver_error

    mock_mysql_connector.connect.side_effect = [
        driver_error("first call fails"),
        mock.MagicMock(name="retry-connection"),
    ]

    conn = _make_connection(minimal_credentials)
    MariaDBConnectionManager.open(conn)

    assert mock_mysql_connector.connect.call_count == 2
    second_call_kwargs = mock_mysql_connector.connect.call_args_list[1].kwargs
    assert second_call_kwargs["database"] == "analytics"
    assert conn.state == "open"


def test_open_raises_failed_to_connect_when_retry_also_fails(
    minimal_credentials, mock_mysql_connector
):
    from dbt.adapters.exceptions.connection import FailedToConnectError

    driver_error = type("DriverError", (Exception,), {})
    mock_mysql_connector.Error = driver_error
    mock_mysql_connector.connect.side_effect = driver_error("nope")

    conn = _make_connection(minimal_credentials)
    with pytest.raises(FailedToConnectError):
        MariaDBConnectionManager.open(conn)

    assert conn.state == "fail"
    assert conn.handle is None


def test_open_retries_attempts_multiple_times_when_configured(mock_mysql_connector):
    creds = MariaDBCredentials(
        server="localhost",
        schema="analytics",
        username="u",
        password="p",
        retries=3,
    )

    driver_error = type("DriverError", (Exception,), {})
    mock_mysql_connector.Error = driver_error

    mock_mysql_connector.connect.side_effect = [
        driver_error("attempt 1 no-db"),
        driver_error("attempt 1 with-db"),
        driver_error("attempt 2 no-db"),
        mock.MagicMock(name="attempt-2-with-db-success"),
    ]

    conn = _make_connection(creds)
    with mock.patch("dbt.adapters.mariadb.connections.time.sleep") as sleep:
        MariaDBConnectionManager.open(conn)

    # 2 attempts × 2 connect calls per attempt = 4
    assert mock_mysql_connector.connect.call_count == 4
    # One backoff sleep between attempt 1 and attempt 2
    sleep.assert_called_once()
    assert conn.state == "open"


def test_cancel_sends_kill_query_and_closes_handle(
    minimal_credentials, mock_mysql_connector
):
    handle = mock.MagicMock()
    handle.connection_id = 4242

    conn = _make_connection(minimal_credentials, state="open")
    conn.handle = handle

    killer = mock.MagicMock()
    cursor = mock.MagicMock()
    killer.cursor.return_value.__enter__.return_value = cursor
    mock_mysql_connector.connect.return_value.__enter__.return_value = killer

    mgr = mock.MagicMock(spec=MariaDBConnectionManager)
    mgr.get_credentials = MariaDBConnectionManager.get_credentials
    mgr._build_connect_kwargs = MariaDBConnectionManager._build_connect_kwargs

    MariaDBConnectionManager.cancel(mgr, conn)

    cursor.execute.assert_called_once_with("KILL QUERY 4242")
    handle.close.assert_called_once()


def test_cancel_is_safe_when_connection_id_missing(
    minimal_credentials, mock_mysql_connector
):
    handle = mock.MagicMock()
    handle.connection_id = None

    conn = _make_connection(minimal_credentials, state="open")
    conn.handle = handle

    mgr = mock.MagicMock(spec=MariaDBConnectionManager)
    mgr.get_credentials = MariaDBConnectionManager.get_credentials
    mgr._build_connect_kwargs = MariaDBConnectionManager._build_connect_kwargs

    MariaDBConnectionManager.cancel(mgr, conn)

    # No KILL QUERY was attempted, but the client-side handle was closed.
    mock_mysql_connector.connect.assert_not_called()
    handle.close.assert_called_once()


def test_cancel_swallows_kill_errors(minimal_credentials, mock_mysql_connector):
    handle = mock.MagicMock()
    handle.connection_id = 7

    conn = _make_connection(minimal_credentials, state="open")
    conn.handle = handle

    mock_mysql_connector.connect.side_effect = RuntimeError("server down")

    mgr = mock.MagicMock(spec=MariaDBConnectionManager)
    mgr.get_credentials = MariaDBConnectionManager.get_credentials
    mgr._build_connect_kwargs = MariaDBConnectionManager._build_connect_kwargs

    # Must NOT raise; cancel is best-effort.
    MariaDBConnectionManager.cancel(mgr, conn)
    handle.close.assert_called_once()


def test_get_response_with_rowcount():
    cursor = mock.MagicMock()
    cursor.rowcount = 42
    resp = MariaDBConnectionManager.get_response(cursor)
    assert resp.code == "SUCCESS"
    assert resp.rows_affected == 42
    assert "SUCCESS 42" in resp._message


def test_get_response_with_none_cursor():
    resp = MariaDBConnectionManager.get_response(None)
    assert resp.code == "SUCCESS"
    assert resp.rows_affected == 0


def test_get_response_with_none_rowcount():
    cursor = mock.MagicMock()
    cursor.rowcount = None
    resp = MariaDBConnectionManager.get_response(cursor)
    assert resp.rows_affected == 0


def test_data_type_code_to_name_roundtrip(mock_mysql_connector):
    mock_mysql_connector.constants.FieldType.desc.values.return_value = [
        (3, "LONG"),
        (253, "VAR_STRING"),
    ]
    assert MariaDBConnectionManager.data_type_code_to_name(3) == "LONG"
    assert MariaDBConnectionManager.data_type_code_to_name(253) == "VAR_STRING"


def test_exception_handler_wraps_driver_errors(mock_mysql_connector):
    class FakeDatabaseError(Exception):
        pass

    class FakeError(Exception):
        pass

    mock_mysql_connector.DatabaseError = FakeDatabaseError
    mock_mysql_connector.Error = FakeError

    mgr = mock.MagicMock(spec=MariaDBConnectionManager)
    mgr.rollback_if_open = mock.MagicMock()

    handler = MariaDBConnectionManager.exception_handler(mgr, "select 1")

    with pytest.raises(DbtDatabaseError, match="bad sql"):
        with handler:
            raise FakeDatabaseError("bad sql")

    mgr.rollback_if_open.assert_called_once()


def test_exception_handler_rewraps_unknown_exceptions_as_runtime_error(
    mock_mysql_connector,
):
    class FakeDatabaseError(Exception):
        pass

    class FakeError(Exception):
        pass

    mock_mysql_connector.DatabaseError = FakeDatabaseError
    mock_mysql_connector.Error = FakeError

    mgr = mock.MagicMock(spec=MariaDBConnectionManager)
    mgr.rollback_if_open = mock.MagicMock()

    handler = MariaDBConnectionManager.exception_handler(mgr, "select 1")

    with pytest.raises(DbtRuntimeError):
        with handler:
            raise ValueError("boom")

    mgr.rollback_if_open.assert_called_once()


def test_exception_handler_preserves_dbt_runtime_errors(mock_mysql_connector):
    class FakeDatabaseError(Exception):
        pass

    mock_mysql_connector.DatabaseError = FakeDatabaseError

    mgr = mock.MagicMock(spec=MariaDBConnectionManager)
    mgr.rollback_if_open = mock.MagicMock()

    handler = MariaDBConnectionManager.exception_handler(mgr, "select 1")
    sentinel = DbtRuntimeError("dbt problem")

    with pytest.raises(DbtRuntimeError) as exc_info:
        with handler:
            raise sentinel

    assert exc_info.value is sentinel
