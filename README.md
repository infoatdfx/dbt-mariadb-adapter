# dbt-mariadb

> Fork of [dbeatty10/dbt-mysql](https://github.com/dbeatty10/dbt-mysql), rescoped to MariaDB only.
> MySQL support has been removed — see [UPSTREAM.md](UPSTREAM.md) for details.

This plugin ports [dbt](https://getdbt.com) functionality to MariaDB.

## Compatibility

| Component | Supported versions |
| --------- | ------------------ |
| dbt-core  | 1.11.x |
| MariaDB   | 11.4 LTS (primary), 11.8 LTS (best-effort) |
| Python    | 3.13 (3.14 under evaluation once dbt-adapters supports it) |

MariaDB 10.x and all MySQL versions are **not** supported by this adapter.

## Installation

```shell
python -m pip install dbt-mariadb
```

## Configuring your profile

```yaml
your_profile_name:
  target: dev
  outputs:
    dev:
      type: mariadb
      server: localhost
      port: 3306
      schema: analytics
      username: your_mariadb_username
      password: your_mariadb_password
      ssl_disabled: True
      charset: utf8mb4
      collation: utf8mb4_uca1400_ai_ci
```

| Option       | Description                                                  | Required? | Example                          |
| ------------ | ------------------------------------------------------------ | --------- | -------------------------------- |
| type         | The adapter to use                                           | Required  | `mariadb`                        |
| server       | The server (hostname) to connect to                          | Required  | `db.example.com`                 |
| port         | The port to use                                              | Optional  | `3306`                           |
| schema       | The schema (MariaDB database) to build models into           | Required  | `analytics`                      |
| username     | The username                                                 | Required  | `dbt_admin`                      |
| password     | The password                                                 | Required  | `correct-horse-battery-staple`   |
| ssl_disabled | Disable TLS                                                  | Optional  | `True` or `False`                |
| charset      | Connection charset                                           | Optional  | `utf8mb4`                        |
| collation    | Connection collation (MariaDB-native, e.g. `utf8mb4_uca1400_ai_ci`) | Optional | `utf8mb4_uca1400_ai_ci`     |

Note: the default MySQL collation `utf8mb4_0900_ai_ci` is **not** available on MariaDB. Use a MariaDB collation such as `utf8mb4_uca1400_ai_ci`.

## Notes on terminology

dbt, ANSI `information_schema` and MariaDB use overlapping but not identical words for "database", "schema" and "catalog". This adapter aligns with dbt's terms: a dbt `schema` is a MariaDB `database`, and MariaDB has no notion of an ANSI catalog.

| information_schema    | dbt (and Postgres)    | MariaDB                        |
| --------------------- | --------------------- | ------------------------------ |
| catalog               | database              | _undefined / not implemented_  |
| schema                | schema                | database                       |
| relation (table/view) | relation              | relation (table/view)          |
| column                | column                | column                         |

Fully-qualified relation names in MariaDB have two parts (`database.table`), not three.

## Running tests

See [tests/README.md](tests/README.md) for details on running the unit and integration tests. A `docker-compose.yml` is provided to spin up a local MariaDB 11.4 instance.

## Migrating from upstream `dbt-mysql`

If you were running `dbeatty10/dbt-mysql` against MariaDB, the migration to `dbt-mariadb` v2.0 is:

1. **Python & dbt-core.** Upgrade your environment to Python 3.13 and dbt-core 1.11.
2. **Package swap.** Uninstall `dbt-mysql` and install `dbt-mariadb` (PyPI or a git-pinned dependency).
3. **Profile `type`.** Replace `type: mysql` / `type: mysql5` with `type: mariadb` in `profiles.yml`. If you had a mix, consolidate onto a single MariaDB target.
4. **Collation.** Replace any `utf8mb4_0900_ai_ci` collation with a MariaDB-native one, e.g. `utf8mb4_uca1400_ai_ci`.
5. **MariaDB upgrade.** Upgrade your server to 11.4 LTS if you're on 10.x. 10.x branches are EOL and no longer tested.
6. **Test.** Run `dbt debug` and your `dbt build` against a non-prod schema before flipping production over.

## Credits

Forked from [`dbeatty10/dbt-mysql`](https://github.com/dbeatty10/dbt-mysql), which itself borrows from [`dbt-spark`](https://github.com/dbt-labs/dbt-spark) and [`dbt-sqlite`](https://github.com/codeforkjeff/dbt-sqlite).
