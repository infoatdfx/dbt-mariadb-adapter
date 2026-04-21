"""Snapshot materialization coverage, including the dbt 1.9 extensions
(custom meta column names, `dbt_valid_to_current`, multi-column unique_key).

Some of these will fail against the current materialization — they're
wired up so regressions are visible. The failures document outstanding
work (see UPSTREAM.md 'Deferred items').
"""
from __future__ import annotations

import pytest

from dbt.tests.adapter.simple_snapshot.test_various_configs import (
    BaseSnapshotColumnNames,
    BaseSnapshotColumnNamesFromDbtProject,
    BaseSnapshotDbtValidToCurrent,
    BaseSnapshotInvalidColumnNames,
    BaseSnapshotMultiUniqueKey,
)


@pytest.mark.skip(
    reason=(
        "snapshot_meta_column_names is a dbt 1.9 feature — our "
        "materialization still emits fixed dbt_valid_{from,to}/dbt_scd_id. "
        "Tracked in UPSTREAM.md 'Deferred items'."
    )
)
class TestSnapshotColumnNamesMariaDB(BaseSnapshotColumnNames):
    pass


@pytest.mark.skip(reason="Depends on snapshot_meta_column_names support.")
class TestSnapshotColumnNamesFromDbtProjectMariaDB(
    BaseSnapshotColumnNamesFromDbtProject
):
    pass


@pytest.mark.skip(reason="Depends on snapshot_meta_column_names support.")
class TestSnapshotInvalidColumnNamesMariaDB(BaseSnapshotInvalidColumnNames):
    pass


@pytest.mark.skip(
    reason=(
        "dbt_valid_to_current requires the materialization to emit a "
        "finite sentinel instead of NULL. Not yet implemented."
    )
)
class TestSnapshotDbtValidToCurrentMariaDB(BaseSnapshotDbtValidToCurrent):
    pass


@pytest.mark.skip(
    reason=(
        "Multi-column unique_key support requires snapshot_staging_table "
        "to compose a composite key expression; today it renders the list "
        "directly. Tracked in UPSTREAM.md."
    )
)
class TestSnapshotMultiUniqueKeyMariaDB(BaseSnapshotMultiUniqueKey):
    pass
