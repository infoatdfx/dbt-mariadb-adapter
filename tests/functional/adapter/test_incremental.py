"""Extended incremental-materialization coverage.

Wires up the widely-used Base* classes from dbt-tests-adapter that the
original upstream suite never exercised. Run these against MariaDB 11.4
to catch on_schema_change regressions, predicate filtering issues, and
merge-exclusion bugs.
"""
from __future__ import annotations

import pytest

from dbt.tests.adapter.incremental.test_incremental_merge_exclude_columns import (
    BaseMergeExcludeColumns,
)
from dbt.tests.adapter.incremental.test_incremental_microbatch import (
    BaseMicrobatch,
)
from dbt.tests.adapter.incremental.test_incremental_on_schema_change import (
    BaseIncrementalOnSchemaChange,
)
from dbt.tests.adapter.incremental.test_incremental_predicates import (
    BaseIncrementalPredicates,
)


class TestIncrementalOnSchemaChangeMariaDB(BaseIncrementalOnSchemaChange):
    pass


class TestIncrementalPredicatesMariaDB(BaseIncrementalPredicates):
    @pytest.fixture(scope="class")
    def project_config_update(self):
        # MariaDB's UPDATE uses different syntax for multi-column predicates;
        # the base class emits ANSI-compatible SQL which MariaDB accepts.
        return {
            "models": {
                "+incremental_predicates": ["id != 2"],
                "+incremental_strategy": "delete+insert",
            }
        }


class TestMergeExcludeColumnsMariaDB(BaseMergeExcludeColumns):
    pass


class TestMicrobatchMariaDB(BaseMicrobatch):
    pass
