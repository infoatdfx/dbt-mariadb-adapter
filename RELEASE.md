# Release Procedure

1. [Bump version](#bump-version)
2. [Distribute](#distribute)
3. [GitHub release](#github-release)

## Bump version

1. Open a branch for the release: `git checkout -b releases/2.0.0`
2. Update [`CHANGELOG.md`](CHANGELOG.md) with the release notes.
3. Bump the version using [`bump-my-version`](https://github.com/callowayproject/bump-my-version):
    - Dry run: `bump-my-version bump --dry-run --verbose --new-version <desired-version> <part>`
    - Apply: `bump-my-version bump --no-tag --new-version <desired-version> <part>`
4. Check the diff with `git diff`.
5. Stage and commit: `git commit -m "Release dbt-mariadb v<desired-version>"`.
6. Push and merge the branch.

## Distribute

Build and publish:

```shell
python -m pip install --upgrade build twine
python -m build
# Optional smoke test against Test PyPI first
twine upload -r testpypi dist/*
# Real publish
twine upload dist/*
```

Alternatively, pin to a git tag from downstream projects if you are not publishing to PyPI.

## GitHub release

1. Create an annotated tag: `git tag -a v<version> -m "dbt-mariadb v<version>"` and push the tag.
2. On GitHub, click _Create a new release_, select the tag, set the title to `dbt-mariadb v<version>`, and paste the changelog entry into the description.
3. Tick "This is a pre-release" for `aN`, `bN`, or `rcN` versions.
