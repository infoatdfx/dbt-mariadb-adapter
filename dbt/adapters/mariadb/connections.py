import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Dict, Optional, Union

import mysql.connector
import mysql.connector.constants

from dbt.adapters.contracts.connection import (
    AdapterResponse,
    Connection,
    Credentials,
)
from dbt.adapters.events.logging import AdapterLogger
from dbt.adapters.exceptions.connection import FailedToConnectError
from dbt.adapters.sql import SQLConnectionManager
from dbt_common.exceptions import DbtDatabaseError, DbtRuntimeError

logger = AdapterLogger("mariadb")

DEFAULT_APPLICATION_NAME = "dbt"


@dataclass
class MariaDBCredentials(Credentials):
    server: str = ""
    unix_socket: Optional[str] = None
    port: Optional[int] = None
    database: Optional[str] = None  # type: ignore[assignment]
    schema: str = ""
    username: Optional[str] = None
    password: Optional[str] = None
    charset: Optional[str] = None
    ssl_disabled: Optional[bool] = None
    collation: Optional[str] = None
    connect_timeout: int = 10
    retries: int = 1
    application_name: str = DEFAULT_APPLICATION_NAME

    _ALIASES = {
        "UID": "username",
        "user": "username",
        "PWD": "password",
        "host": "server",
    }

    def __post_init__(self):
        # dbt "database" and MariaDB "schema" refer to the same thing. Accept
        # database=None (most common) or database==schema; anything else is a
        # configuration error we want to surface early.
        if self.database is not None and self.database != self.schema:
            raise DbtRuntimeError(
                f"    schema: {self.schema} \n"
                f"    database: {self.database} \n"
                f"On MariaDB, database must be omitted"
                f" or have the same value as schema."
            )
        # Normalise to None so downstream code can treat dbt-database as absent.
        self.database = None

    @property
    def type(self) -> str:
        return "mariadb"

    @property
    def unique_field(self) -> str:
        return self.schema

    def _connection_keys(self):
        """Keys displayed in `dbt debug`."""
        return (
            "server",
            "unix_socket",
            "port",
            "database",
            "schema",
            "user",
            "connect_timeout",
            "retries",
            "application_name",
        )


class MariaDBConnectionManager(SQLConnectionManager):
    TYPE = "mariadb"

    @classmethod
    def open(cls, connection: Connection) -> Connection:
        if connection.state == "open":
            logger.debug("Connection is already open, skipping open.")
            return connection

        credentials: MariaDBCredentials = cls.get_credentials(connection.credentials)
        base_kwargs = cls._build_connect_kwargs(credentials)

        # Retry with exponential backoff. `retries == 1` (default) means a
        # single attempt; `retries == 3` means up to 3 attempts.
        attempts = max(credentials.retries, 1)
        last_error: Optional[Exception] = None

        for attempt in range(1, attempts + 1):
            try:
                connection.handle = mysql.connector.connect(**base_kwargs)
                connection.state = "open"
                return connection
            except mysql.connector.Error as e:
                last_error = e
                logger.debug(
                    "MariaDB connection attempt %d/%d without `database` failed: %s",
                    attempt,
                    attempts,
                    e,
                )

                # Retry immediately with `database` included — this matches the
                # upstream behaviour for MariaDB/MySQL where the user needs the
                # schema to exist before pointing at it.
                with_database = {**base_kwargs, "database": credentials.schema}
                try:
                    connection.handle = mysql.connector.connect(**with_database)
                    connection.state = "open"
                    return connection
                except mysql.connector.Error as retry_err:
                    last_error = retry_err
                    logger.debug(
                        "Retry with `database=%s` also failed on attempt %d/%d: %s",
                        credentials.schema,
                        attempt,
                        attempts,
                        retry_err,
                    )

            if attempt < attempts:
                # Exponential backoff: 1, 2, 4, ... seconds (max 16).
                sleep_for = min(2 ** (attempt - 1), 16)
                logger.debug("Sleeping %d seconds before retry.", sleep_for)
                time.sleep(sleep_for)

        # All attempts exhausted.
        connection.handle = None
        connection.state = "fail"
        raise FailedToConnectError(str(last_error))

    @staticmethod
    def _build_connect_kwargs(credentials: MariaDBCredentials) -> Dict[str, Any]:
        kwargs: Dict[str, Any] = {
            "user": credentials.username,
            "passwd": credentials.password,
            "buffered": True,
            "connection_timeout": credentials.connect_timeout,
        }
        # mysql-connector-python exposes init-command, which MariaDB honours:
        # we use it to tag sessions so they can be spotted in `SHOW PROCESSLIST`.
        if credentials.application_name:
            # Escape single quotes defensively even though this value comes
            # from the profile, not end-user SQL.
            safe_name = credentials.application_name.replace("'", "''")
            kwargs["init_command"] = f"SET SESSION program_name = '{safe_name}'"

        if credentials.ssl_disabled:
            kwargs["ssl_disabled"] = credentials.ssl_disabled
        if credentials.server:
            kwargs["host"] = credentials.server
        elif credentials.unix_socket:
            kwargs["unix_socket"] = credentials.unix_socket
        if credentials.port:
            kwargs["port"] = credentials.port
        if credentials.charset:
            kwargs["charset"] = credentials.charset
        if credentials.collation:
            kwargs["collation"] = credentials.collation
        return kwargs

    @classmethod
    def get_credentials(cls, credentials: MariaDBCredentials) -> MariaDBCredentials:
        return credentials

    def cancel(self, connection: Connection) -> None:
        """Terminate an in-flight query on the server, then close the handle.

        Merely closing the client socket leaves the query running on the
        MariaDB server until it completes — wasteful and confusing for users
        who expect Ctrl-C to mean "stop now". We send `KILL QUERY <connection_id>`
        via a short-lived auxiliary connection so we don't deadlock on the
        handle we're trying to cancel.
        """
        handle = connection.handle
        connection_id: Optional[int] = None
        try:
            connection_id = getattr(handle, "connection_id", None)
        except Exception:  # pragma: no cover — defensive
            connection_id = None

        if connection_id is not None:
            try:
                creds: MariaDBCredentials = self.get_credentials(connection.credentials)
                kill_kwargs = self._build_connect_kwargs(creds)
                with mysql.connector.connect(**kill_kwargs) as killer:
                    with killer.cursor() as cur:
                        cur.execute(f"KILL QUERY {int(connection_id)}")
                logger.debug("Sent KILL QUERY %s", connection_id)
            except Exception as e:
                # If the kill itself fails, fall through and still close the
                # client-side handle — don't let cleanup raise.
                logger.debug("KILL QUERY %s failed: %s", connection_id, e)

        try:
            if handle is not None:
                handle.close()
        except Exception as e:  # pragma: no cover
            logger.debug("Closing MariaDB handle raised: %s", e)

    @contextmanager
    def exception_handler(self, sql: str):
        try:
            yield

        except mysql.connector.DatabaseError as e:
            logger.debug("MariaDB error: {}".format(str(e)))

            try:
                self.rollback_if_open()
            except mysql.connector.Error:
                logger.debug("Failed to release connection!")
                pass

            raise DbtDatabaseError(str(e).strip()) from e

        except Exception as e:
            logger.debug("Error running SQL: {}", sql)
            logger.debug("Rolling back transaction.")
            self.rollback_if_open()
            if isinstance(e, DbtRuntimeError):
                # Preserve internal dbt exceptions untouched; they often carry
                # diagnostic info the base handler would discard.
                raise

            raise DbtRuntimeError(str(e)) from e

    @classmethod
    def get_response(cls, cursor) -> AdapterResponse:
        code = "SUCCESS"
        num_rows = 0

        if cursor is not None and cursor.rowcount is not None:
            num_rows = cursor.rowcount

        # mysql-connector-python does not expose a meaningful status code for
        # successful statements, so we return a synthetic one.
        return AdapterResponse(
            _message="{} {}".format(code, num_rows), rows_affected=num_rows, code=code
        )

    @classmethod
    def data_type_code_to_name(cls, type_code: Union[int, str]) -> str:
        field_type_values = mysql.connector.constants.FieldType.desc.values()
        mapping = {code: name for (code, name) in field_type_values}
        return mapping[type_code]
