"""`dbt docs generate` coverage — makes sure the catalog builds cleanly
against a MariaDB project, including source refs and ephemeral models.
"""
from __future__ import annotations

from dbt.tests.adapter.basic.test_docs_generate import (
    BaseDocsGenerate,
    BaseDocsGenReferences,
)


class TestDocsGenerateMariaDB(BaseDocsGenerate):
    pass


class TestDocsGenReferencesMariaDB(BaseDocsGenReferences):
    pass
