# Changelog

## dbt-mariadb 2.0.0 (unreleased)

This is the first release of `dbt-mariadb` as a hard fork of
[`dbeatty10/dbt-mysql`](https://github.com/dbeatty10/dbt-mysql) at commit
`09e076f7`. See [UPSTREAM.md](UPSTREAM.md) for fork provenance.

### Breaking changes

- Dropped all MySQL support. The `mysql` and `mysql5` adapters are gone. This fork is MariaDB-only.
- Minimum MariaDB version is now **11.4 LTS**. Older (EOL) 10.x versions are not supported.
- Minimum dbt-core is **1.11**. Earlier versions are not supported.
- Minimum Python is **3.13**.
- Package renamed from `dbt-mysql` to `dbt-mariadb`.
- Default MySQL collation `utf8mb4_0900_ai_ci` is no longer a valid profile value — use a MariaDB-native collation such as `utf8mb4_uca1400_ai_ci`.

### Added

- MariaDB 11.x-specific functional tests: JSON columns, fractional-second timestamps, SEQUENCE objects, 12k-row incremental merges, `information_schema.COLUMNS` shape, schema lifecycle.
- 70+ database-free unit tests covering credentials, connection kwargs construction and retry flow, adapter SQL primitives, relation/column policies, and macro structure.
- GitHub Actions CI: lint + unit on every push/PR; integration against MariaDB 11.4 (blocking) and 11.8 (best effort) with weekly scheduled runs.
- Dependabot for weekly `pip` and `github-actions` updates, grouped by family.

### Changed

- Migrated to the `dbt-adapters` 1.22 architecture (post-1.8 decoupling). All imports now resolve against `dbt.adapters.*` and `dbt_common.*`.
- Repository layout: `dbt/adapters/mysql*` and `dbt/include/mysql*` removed.

### Deferred

- Driver swap from `mysql-connector-python` to the official `mariadb` PyPI package. Motivation and conditions documented in [UPSTREAM.md](UPSTREAM.md).

---

## Historical upstream changelog (dbt-mysql 0.x – 1.x)

The entries below are preserved for provenance. They describe upstream `dbt-mysql` releases before the fork and all issue/PR links point at the upstream repository.

### Upstream unreleased

- Migrate CircleCI to GitHub Actions ([#120](https://github.com/dbeatty10/dbt-mysql/issues/120))
- Support dbt v1.4 ([#146](https://github.com/dbeatty10/dbt-mysql/pull/146))
- Support dbt v1.5 ([#145](https://github.com/dbeatty10/dbt-mysql/issues/145))
- Support connecting via UNIX sockets ([#164](https://github.com/dbeatty10/dbt-mysql/issues/164))
- Support Black & MyPy pre-commit hooks ([#138](https://github.com/dbeatty10/dbt-mysql/issues/138))
- Fix incremental composite keys ([#144](https://github.com/dbeatty10/dbt-mysql/issues/144))
- Fix UnicodeDecodeErorr on setup.py ([#160](https://github.com/dbeatty10/dbt-mysql/issues/160))

### Upstream dbt-mysql 1.1.0 (Feb 5, 2023)

- Support dbt v1.1 ([#100](https://github.com/dbeatty10/dbt-mysql/pull/100))
- Clearer exception for invalid `database` config ([#110](https://github.com/dbeatty10/dbt-mysql/issues/110), [#111](https://github.com/dbeatty10/dbt-mysql/pull/111))
- Document supported Python versions ([#115](https://github.com/dbeatty10/dbt-mysql/issues/115), [#116](https://github.com/dbeatty10/dbt-mysql/pull/116))
- docker-compose for local testing ([#104](https://github.com/dbeatty10/dbt-mysql/pull/104))
- New adapter testing framework ([#109](https://github.com/dbeatty10/dbt-mysql/pull/109))

### Upstream dbt-mysql 1.0.0 and earlier

Older upstream entries (0.18.0 through 1.0.0) covered initial ODBC support, the switch to a DB API 2.0 driver, the split into MySQL 5.x / 8.x adapters, and integration testing against MariaDB 10.5. They are not reproduced here; see the upstream repository's git history for details.
