import pytest

from dbt_common.exceptions import DbtRuntimeError

from dbt.adapters.mariadb.relation import (
    MariaDBIncludePolicy,
    MariaDBQuotePolicy,
    MariaDBRelation,
)


def test_quote_policy_defaults():
    policy = MariaDBQuotePolicy()
    assert policy.database is False
    assert policy.schema is True
    assert policy.identifier is True


def test_include_policy_defaults():
    policy = MariaDBIncludePolicy()
    assert policy.database is False
    assert policy.schema is True
    assert policy.identifier is True


def test_quote_character_is_backtick():
    rel = MariaDBRelation.create(schema="analytics", identifier="my_table", type="table")
    assert rel.quote_character == "`"


def test_rendered_relation_uses_backticks():
    rel = MariaDBRelation.create(schema="analytics", identifier="my_table", type="table")
    rendered = rel.render()
    assert "`analytics`" in rendered
    assert "`my_table`" in rendered


def test_post_init_rejects_database_schema_mismatch():
    with pytest.raises(DbtRuntimeError, match="Cannot set `database`"):
        MariaDBRelation.create(
            database="other_db", schema="analytics", identifier="my_table", type="table"
        )


def test_post_init_allows_database_equal_to_schema():
    # Should not raise
    rel = MariaDBRelation.create(
        database="analytics", schema="analytics", identifier="my_table", type="table"
    )
    assert rel.schema == "analytics"


def test_render_raises_when_both_database_and_schema_included():
    rel = MariaDBRelation.create(
        schema="analytics",
        identifier="my_table",
        type="table",
        include_policy=MariaDBIncludePolicy(database=True, schema=True, identifier=True),
    )
    with pytest.raises(DbtRuntimeError, match="only one can be set"):
        rel.render()
