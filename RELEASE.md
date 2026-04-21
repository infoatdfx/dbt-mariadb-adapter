# Release Procedure

1. [Prepare changelog](#prepare-changelog)
2. [Bump version](#bump-version)
3. [Build & publish](#build--publish)
4. [GitHub release](#github-release)

## Prepare changelog

We use [changie](https://changie.dev/) to collect per-PR changelog entries and
assemble them at release time.

```shell
# Every contributor runs this as part of their PR:
changie new

# At release time, consolidate all unreleased entries into CHANGELOG.md:
changie batch <version>   # e.g. changie batch 2.0.0
changie merge             # appends the batched section to CHANGELOG.md
git add .changes CHANGELOG.md
git commit -m "chore: release notes for v<version>"
```

## Bump version

```shell
git checkout -b releases/<version>
bump-my-version bump --dry-run --verbose --new-version <version> <part>
bump-my-version bump --no-tag --new-version <version> <part>
git diff
git commit -am "Release dbt-mariadb v<version>"
git push -u origin releases/<version>
```

Merge the release branch into `main` via PR.

## Build & publish

```shell
python -m pip install --upgrade build twine
python -m build
twine check dist/*
twine upload -r testpypi dist/*      # optional smoke test
twine upload dist/*
```

Or pin downstream projects to the resulting git tag if you are not publishing
to PyPI.

## GitHub release

```shell
git tag -a v<version> -m "dbt-mariadb v<version>"
git push origin v<version>
```

Then create a new release on GitHub pointing at the tag. Paste the changie-
generated section from `CHANGELOG.md` into the description. Tick
"This is a pre-release" for `aN` / `bN` / `rcN` versions.
