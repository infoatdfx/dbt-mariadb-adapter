# Upstream provenance

This repository is a hard fork of [dbeatty10/dbt-mysql](https://github.com/dbeatty10/dbt-mysql), rescoped to exclusively support MariaDB.

## Fork metadata

| Field | Value |
| ----- | ----- |
| Upstream repository | `dbeatty10/dbt-mysql` |
| Upstream commit at fork | `09e076f7203ffe1486f3bf8394ec3bb9c5b38ddc` (Mwallace/merge 1.7 to main) |
| Upstream commit date | 2024-04-26 |
| Fork date | 2026-04-21 |
| New package name | `dbt-mariadb` |

## Scope of the fork

**In scope:**

- `dbt-core` 1.11.x on the `dbt-adapters` 1.22.x decoupled architecture (post-1.8).
- MariaDB 11.4 LTS (primary) and MariaDB 11.8 LTS (best-effort secondary).
- Python 3.13+ (3.14 once `dbt-adapters` supports it).
- Full `dbt-tests-adapter` coverage against MariaDB 11.4.

**Out of scope (deliberately removed):**

- All MySQL support. The `mysql` and `mysql5` adapters shipped by upstream have been deleted. This fork will not accept MySQL changes.
- MariaDB 10.x. All 10.x branches are at or near end-of-life and are not tested.
- `dbt-core` < 1.11, Python < 3.13.
- dbt Fusion (Rust) integration — a separate conversation later.

## Release strategy

The first release of this fork is tagged `v2.0.0`. That bump is intentional and marks a breaking change versus upstream `dbt-mysql` 1.7.x: MySQL support is gone, minimum MariaDB is 11.4, minimum Python is 3.13, minimum dbt-core is 1.11.

## Deferred items

- **Driver swap to `mariadb` (PyPI) package — deferred.** Fase 4 of the fork plan evaluated swapping `mysql-connector-python` for the official [`mariadb`](https://pypi.org/project/mariadb/) Python connector. The driver is MariaDB-native and gets actively tested against 11.x, but it is not pure Python: it requires `libmariadb-dev` (or `mariadb-connector-c` via Homebrew) as a system dependency on every developer machine, CI runner, and container image. `mysql-connector-python` (pinned to `>=9.0.0`) is pure Python, speaks MariaDB's wire protocol reliably, and keeps the install surface simple. We are keeping `mysql-connector-python` for the v2.0.0 release and revisiting the driver swap once the system-library story is acceptable across our deploy targets. When reopened, the scope is documented in the plan's Fase 4.
