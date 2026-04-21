from dbt.tests.adapter.incremental.test_incremental_unique_id import (
    BaseIncrementalUniqueKey,
)

from dbt.tests.adapter.basic.test_base import BaseSimpleMaterializations
from dbt.tests.adapter.basic.test_singular_tests import BaseSingularTests
from dbt.tests.adapter.basic.test_singular_tests_ephemeral import (
    BaseSingularTestsEphemeral,
)
from dbt.tests.adapter.basic.test_empty import BaseEmpty
from dbt.tests.adapter.basic.test_ephemeral import BaseEphemeral
from dbt.tests.adapter.basic.test_incremental import BaseIncremental
from dbt.tests.adapter.basic.test_generic_tests import BaseGenericTests
from dbt.tests.adapter.basic.test_snapshot_check_cols import (
    BaseSnapshotCheckCols,
)
from dbt.tests.adapter.basic.test_snapshot_timestamp import (
    BaseSnapshotTimestamp,
)
from dbt.tests.adapter.basic.test_adapter_methods import BaseAdapterMethod
from dbt.tests.util import run_dbt, check_relations_equal


class TestSimpleMaterializationsMariaDB(BaseSimpleMaterializations):
    pass


class TestSingularTestsMariaDB(BaseSingularTests):
    pass


class TestSingularTestsEphemeralMariaDB(BaseSingularTestsEphemeral):
    pass


class TestEmptyMariaDB(BaseEmpty):
    pass


class TestEphemeralMariaDB(BaseEphemeral):
    pass


class TestIncrementalMariaDB(BaseIncremental):
    pass


class TestIncrementalUniqueKeyMariaDB(BaseIncrementalUniqueKey):
    pass


class TestGenericTestsMariaDB(BaseGenericTests):
    pass


class TestSnapshotCheckColsMariaDB(BaseSnapshotCheckCols):
    pass


class TestSnapshotTimestampMariaDB(BaseSnapshotTimestamp):
    pass


class TestBaseAdapterMethodMariaDB(BaseAdapterMethod):
    def test_adapter_methods(self, project, equal_tables):
        result = run_dbt()
        assert len(result) == 3
        check_relations_equal(project.adapter, equal_tables)
