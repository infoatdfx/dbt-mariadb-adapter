"""Cross-db utility macro coverage.

Every `dbt.<macro>` dispatch point we ship gets exercised against the
canonical expected output from dbt-tests-adapter. If the macro doesn't
match postgres semantics exactly (e.g. our date_trunc always returns
DATETIME rather than DATE for 'day'), override `models__*_expected_sql`
in the subclass with the MariaDB-correct expected output.
"""
from __future__ import annotations

from dbt.tests.adapter.utils.test_any_value import BaseAnyValue
from dbt.tests.adapter.utils.test_array_append import BaseArrayAppend
from dbt.tests.adapter.utils.test_array_concat import BaseArrayConcat
from dbt.tests.adapter.utils.test_array_construct import BaseArrayConstruct
from dbt.tests.adapter.utils.test_bool_or import BaseBoolOr
from dbt.tests.adapter.utils.test_cast_bool_to_text import BaseCastBoolToText
from dbt.tests.adapter.utils.test_concat import BaseConcat
from dbt.tests.adapter.utils.test_date_trunc import BaseDateTrunc
from dbt.tests.adapter.utils.test_dateadd import BaseDateAdd
from dbt.tests.adapter.utils.test_datediff import BaseDateDiff
from dbt.tests.adapter.utils.test_escape_single_quotes import (
    BaseEscapeSingleQuotesQuote,
)
from dbt.tests.adapter.utils.test_except import BaseExcept
from dbt.tests.adapter.utils.test_hash import BaseHash
from dbt.tests.adapter.utils.test_intersect import BaseIntersect
from dbt.tests.adapter.utils.test_last_day import BaseLastDay
from dbt.tests.adapter.utils.test_length import BaseLength
from dbt.tests.adapter.utils.test_listagg import BaseListagg
from dbt.tests.adapter.utils.test_position import BasePosition
from dbt.tests.adapter.utils.test_replace import BaseReplace
from dbt.tests.adapter.utils.test_right import BaseRight
from dbt.tests.adapter.utils.test_safe_cast import BaseSafeCast
from dbt.tests.adapter.utils.test_split_part import BaseSplitPart
from dbt.tests.adapter.utils.test_string_literal import BaseStringLiteral


class TestAnyValueMariaDB(BaseAnyValue):
    pass


class TestBoolOrMariaDB(BaseBoolOr):
    pass


class TestCastBoolToTextMariaDB(BaseCastBoolToText):
    pass


class TestConcatMariaDB(BaseConcat):
    pass


class TestDateTruncMariaDB(BaseDateTrunc):
    pass


class TestDateAddMariaDB(BaseDateAdd):
    pass


class TestDateDiffMariaDB(BaseDateDiff):
    pass


class TestEscapeSingleQuotesMariaDB(BaseEscapeSingleQuotesQuote):
    pass


class TestExceptMariaDB(BaseExcept):
    pass


class TestHashMariaDB(BaseHash):
    pass


class TestIntersectMariaDB(BaseIntersect):
    pass


class TestLastDayMariaDB(BaseLastDay):
    pass


class TestLengthMariaDB(BaseLength):
    pass


class TestListaggMariaDB(BaseListagg):
    pass


class TestPositionMariaDB(BasePosition):
    pass


class TestReplaceMariaDB(BaseReplace):
    pass


class TestRightMariaDB(BaseRight):
    pass


class TestSafeCastMariaDB(BaseSafeCast):
    pass


class TestSplitPartMariaDB(BaseSplitPart):
    pass


class TestStringLiteralMariaDB(BaseStringLiteral):
    pass


# Array-backed macros — our implementation uses JSON, so these may need
# MariaDB-specific fixtures. Marking them explicitly so the failure mode
# is "tests needs MariaDB-shaped expected output", not "macro missing".
class TestArrayAppendMariaDB(BaseArrayAppend):
    pass


class TestArrayConcatMariaDB(BaseArrayConcat):
    pass


class TestArrayConstructMariaDB(BaseArrayConstruct):
    pass
