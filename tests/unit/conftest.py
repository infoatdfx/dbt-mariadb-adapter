"""Shared fixtures for dbt-mariadb unit tests.

Unit tests must not touch a live database. Anything driver-shaped is patched
via `unittest.mock`.
"""
from __future__ import annotations

from unittest import mock

import pytest

from dbt.adapters.mariadb.connections import MariaDBCredentials


@pytest.fixture
def minimal_credentials_kwargs() -> dict:
    return {
        "server": "localhost",
        "schema": "analytics",
        "username": "dbt",
        "password": "secret",
    }


@pytest.fixture
def minimal_credentials(minimal_credentials_kwargs) -> MariaDBCredentials:
    return MariaDBCredentials(**minimal_credentials_kwargs)


@pytest.fixture
def full_credentials() -> MariaDBCredentials:
    return MariaDBCredentials(
        server="db.internal",
        port=3307,
        schema="analytics",
        username="dbt",
        password="secret",
        charset="utf8mb4",
        collation="utf8mb4_uca1400_ai_ci",
        ssl_disabled=True,
    )


@pytest.fixture
def mock_mysql_connector():
    """Patch the driver module imported by `connections` so unit tests don't
    hit a real server."""
    with mock.patch("dbt.adapters.mariadb.connections.mysql.connector") as driver:
        yield driver
