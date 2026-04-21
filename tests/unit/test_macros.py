"""Static checks on macro files.

Full Jinja rendering requires a live dbt adapter context — too heavy for a
pure unit test. Instead, we make sure the expected macros exist, are named
with the `mariadb__` dispatch prefix, and contain the SQL fragments that
downstream materialisations rely on. Any regression that renames or
accidentally drops a macro will fail here instantly.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

from dbt.include import mariadb as mariadb_include


MACROS_ROOT = Path(mariadb_include.PACKAGE_PATH) / "macros"


def _read_all_macros() -> str:
    return "\n".join(p.read_text() for p in MACROS_ROOT.rglob("*.sql"))


def _defined_macros(sql: str) -> set[str]:
    return set(re.findall(r"{%\s*macro\s+([a-zA-Z0-9_]+)\s*\(", sql))


@pytest.fixture(scope="module")
def all_sql() -> str:
    return _read_all_macros()


@pytest.fixture(scope="module")
def macro_names(all_sql) -> set[str]:
    return _defined_macros(all_sql)


@pytest.mark.parametrize(
    "macro",
    [
        "mariadb__create_table_as",
        "mariadb__create_view_as",
        "mariadb__drop_relation",
        "mariadb__rename_relation",
        "mariadb__list_schemas",
        "mariadb__list_relations_without_caching",
        "mariadb__create_schema",
        "mariadb__drop_schema",
        "mariadb__truncate_relation",
        "mariadb__current_timestamp",
        "mariadb__check_schema_exists",
        "mariadb__get_columns_in_relation",
        "mariadb__generate_database_name",
        "mariadb__get_phony_data_for_type",
        "mariadb__get_empty_schema_sql",
        "mariadb__get_incremental_append_sql",
        "mariadb__get_incremental_delete_insert_sql",
        "mariadb__get_incremental_merge_sql",
        "mariadb__get_incremental_microbatch_sql",
        "mariadb__get_incremental_default_sql",
    ],
)
def test_macro_is_defined(macro, macro_names):
    assert macro in macro_names, f"macro {macro} missing from package"


@pytest.mark.parametrize(
    "macro",
    [
        "mariadb__any_value",
        "mariadb__bool_or",
        "mariadb__cast_bool_to_text",
        "mariadb__dateadd",
        "mariadb__datediff",
        "mariadb__date_trunc",
        "mariadb__last_day",
        "mariadb__listagg",
        "mariadb__split_part",
        "mariadb__safe_cast",
        "mariadb__hash",
        "mariadb__position",
        "mariadb__right",
        "mariadb__except",
        "mariadb__intersect",
        "mariadb__escape_single_quotes",
        "mariadb__array_construct",
        "mariadb__array_append",
        "mariadb__array_concat",
        "mariadb__generate_series",
    ],
)
def test_utility_macro_is_defined(macro, macro_names):
    """Every dbt.* utility dispatch point must resolve on this adapter."""
    assert macro in macro_names, f"utility macro {macro} missing"


def test_create_table_as_supports_contract_enforcement(all_sql):
    # Contract enforcement must go through get_table_columns_and_constraints
    assert "get_table_columns_and_constraints" in all_sql
    assert "get_assert_columns_equivalent" in all_sql


def test_rename_relation_is_two_step(all_sql):
    # MariaDB's `RENAME TABLE` fails when target exists; we drop first, then rename.
    # Both statements must appear inside mariadb__rename_relation.
    match = re.search(
        r"{%\s*macro\s+mariadb__rename_relation.*?{%\s*endmacro\s*%}",
        all_sql,
        re.DOTALL,
    )
    assert match, "mariadb__rename_relation macro not found"
    body = match.group(0)
    assert "drop" in body.lower()
    assert "rename table" in body.lower()


def test_list_relations_returns_four_columns(all_sql):
    # impl.py expects exactly 4 columns: (database, name, schema, type)
    match = re.search(
        r"{%\s*macro\s+mariadb__list_relations_without_caching.*?{%\s*endmacro\s*%}",
        all_sql,
        re.DOTALL,
    )
    assert match
    body = match.group(0)
    assert "table_name" in body
    assert "table_schema" in body
    assert "table_type" in body


def test_phony_data_for_type_covers_expected_branches(all_sql):
    match = re.search(
        r"{%\s*macro\s+mariadb__get_phony_data_for_type.*?{%\s*endmacro\s*%}",
        all_sql,
        re.DOTALL,
    )
    assert match
    body = match.group(0).lower()
    for branch in ("integer", "text", "integer unsigned", "integer signed"):
        assert branch in body, f"phony branch {branch} missing"


def test_current_timestamp_uses_function_form(all_sql):
    match = re.search(
        r"{%\s*macro\s+mariadb__current_timestamp.*?{%\s*endmacro\s*%}",
        all_sql,
        re.DOTALL,
    )
    assert match
    assert "current_timestamp()" in match.group(0)


def test_catalog_macro_excludes_system_schemas():
    catalog = (MACROS_ROOT / "catalog.sql").read_text()
    for system in ("information_schema", "performance_schema", "mysql", "sys"):
        assert system in catalog, f"catalog query must exclude {system}"


def test_sample_profile_parses():
    sample = Path(mariadb_include.PACKAGE_PATH) / "sample_profiles.yml"
    data = yaml.safe_load(sample.read_text())
    assert "default" in data
    dev = data["default"]["outputs"]["dev"]
    assert dev["type"] == "mariadb"


def test_unsupported_materializations_raise_clear_errors(all_sql):
    # The stubs live in macros/materializations/unsupported.sql and must
    # raise a compiler error explaining the alternative.
    for name in ("materialized_view", "dynamic_table"):
        pattern = (
            r"{%\s*materialization\s+" + name + r"\s*,\s*adapter='mariadb'\s*%}"
            r".*?raise_compiler_error.*?"
            r"{%\s*endmaterialization\s*%}"
        )
        assert re.search(pattern, all_sql, re.DOTALL), (
            f"expected rejection stub for materialization {name}"
        )


def test_dbt_project_yml_declares_macros():
    project = Path(mariadb_include.PACKAGE_PATH) / "dbt_project.yml"
    data = yaml.safe_load(project.read_text())
    assert data["name"] == "dbt_mariadb"
    assert data["macro-paths"] == ["macros"]
