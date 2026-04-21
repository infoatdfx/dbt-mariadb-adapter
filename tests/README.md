# Testing dbt-mariadb

## Overview

1. Set environment variables (or copy `.env.example` to `.env`).
2. Start a MariaDB container via `docker-compose`.
3. Run unit tests and/or functional tests.

## Environment variables

| Variable | Default | Purpose |
| -------- | ------- | ------- |
| `DBT_MARIADB_SERVER_NAME` | `localhost` | MariaDB host |
| `DBT_MARIADB_USERNAME`    | `root`      | MariaDB user |
| `DBT_MARIADB_PASSWORD`    | `dbt`       | MariaDB password |
| `DBT_MARIADB_PORT`        | `3307`      | Port exposed by the MariaDB 11.4 container |
| `DBT_MARIADB_118_PORT`    | `3308`      | Port exposed by the MariaDB 11.8 container |

```shell
cp .env.example .env
$EDITOR .env
```

## Start MariaDB

```shell
# MariaDB 11.4 (primary test target)
docker-compose up -d mariadb-11-4

# MariaDB 11.8 (best-effort secondary)
docker-compose up -d mariadb-11-8
```

Stop with `docker-compose down`.

## Run tests

Unit tests (no database required):

```shell
make test-unit
```

Functional tests against MariaDB 11.4:

```shell
make test-functional
```

Functional tests against MariaDB 11.8 (best effort):

```shell
make test-functional-118
```

Everything:

```shell
make test-all
```

Run a single test:

```shell
DBT_MARIADB_PORT=3307 pytest -v tests/functional/adapter/test_basic.py::TestEmptyMariaDB::test_empty
```
