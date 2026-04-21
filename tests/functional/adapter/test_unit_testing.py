"""Unit-test materialization coverage (dbt 1.8+)."""
from __future__ import annotations

from dbt.tests.adapter.unit_testing.test_case_insensitivity import (
    BaseUnitTestCaseInsensivity,
)
from dbt.tests.adapter.unit_testing.test_invalid_input import (
    BaseUnitTestInvalidInput,
)
from dbt.tests.adapter.unit_testing.test_quoted_reserved_word_column_names import (
    BaseUnitTestQuotedReservedWordColumnNames,
)
from dbt.tests.adapter.unit_testing.test_types import (
    BaseUnitTestingTypes,
)


class TestUnitTestingTypesMariaDB(BaseUnitTestingTypes):
    pass


class TestUnitTestCaseInsensivityMariaDB(BaseUnitTestCaseInsensivity):
    pass


class TestUnitTestInvalidInputMariaDB(BaseUnitTestInvalidInput):
    pass


class TestUnitTestQuotedReservedWordColumnNamesMariaDB(
    BaseUnitTestQuotedReservedWordColumnNames
):
    pass
