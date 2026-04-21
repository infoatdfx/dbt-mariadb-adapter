"""Relation-type lifecycle: view -> table -> incremental -> view."""
from __future__ import annotations

from dbt.tests.adapter.relations.test_changing_relation_type import (
    BaseChangeRelationTypeValidator,
)


class TestChangeRelationTypeMariaDB(BaseChangeRelationTypeValidator):
    pass
