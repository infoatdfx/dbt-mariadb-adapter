# Contributing

Contributions are welcome. This fork is scoped to **MariaDB 11.4+**; MySQL contributions will not be accepted.

## Ways to contribute

### Report bugs

File issues at the project issue tracker. Please include:

- MariaDB server version (`SELECT VERSION();`).
- Python version (`python --version`).
- dbt version (`dbt --version`).
- A minimal reproduction: the dbt model or command, the adapter error, and the state of the target database.

### Propose features

Open an issue describing the use case before starting larger work, so scope can be agreed on first.

### Contribute code

1. Fork the repository on GitHub.
2. Clone your fork.
3. Install in editable mode with the dev dependencies:

    ```shell
    python3 -m venv .venv
    source .venv/bin/activate
    python3 -m pip install --upgrade pip
    python3 -m pip install -e . -r dev-requirements.txt
    pre-commit install
    ```

4. Create a feature branch:

    ```shell
    git checkout -b feature/short-description
    ```

5. Run the tests:

    ```shell
    make test-unit                # unit tests, no DB required
    docker-compose up -d mariadb-11-4
    DBT_MARIADB_PORT=3307 make test-functional
    ```

6. Add a changelog entry with [changie](https://changie.dev/):

    ```shell
    changie new
    ```

    Pick a kind (Breaking / Features / Fixes / Under the Hood / Dependencies / Security / Docs), fill in the body, and optionally an issue/PR number and your GitHub handle. The generated file lives under `.changes/unreleased/` — commit it with your code. CI verifies that every non-docs PR ships a corresponding `.changes/unreleased/` entry.
7. Commit (conventional commits preferred) and push your branch.
8. Open a pull request against `main`. The PR description should state which MariaDB version(s) you tested against.

## Supported versions

| Component | Supported |
| --------- | --------- |
| dbt-core  | 1.11.x    |
| MariaDB   | 11.4 LTS (primary), 11.8 LTS (best effort) |
| Python    | 3.13      |

Contributions that reintroduce MySQL compatibility, target MariaDB 10.x, or loosen the Python/dbt-core minimums will not be merged.
