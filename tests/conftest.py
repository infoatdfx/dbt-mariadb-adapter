import os

import pytest

# Import the functional fixtures as a plugin
# Note: fixtures with session scope need to be local
pytest_plugins = ["dbt.tests.fixtures.project"]


# dbt will supply a unique schema per test, so we do not specify 'schema' here
def _mariadb_target():
    return {
        "type": "mariadb",
        "port": int(os.getenv("DBT_MARIADB_PORT", "3306")),
        "server": os.getenv("DBT_MARIADB_SERVER_NAME", "localhost"),
        "username": os.getenv("DBT_MARIADB_USERNAME", "root"),
        "password": os.getenv("DBT_MARIADB_PASSWORD", "dbt"),
    }


@pytest.fixture(scope="session")
def dbt_profile_target():
    return _mariadb_target()
