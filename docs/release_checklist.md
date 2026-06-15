# Release Checklist

Use this before tagging a new release.

---

## Pre-release

- [ ] All tests pass on Python 3.9, 3.10, 3.11, 3.12
  ```bash
  python3 -m pytest --tb=short -q
  ```
- [ ] CI badge is green on `main`
- [ ] `CHANGELOG.md` is updated — move items from `[Unreleased]` to the new version section
- [ ] `pyproject.toml` version is bumped (follows semantic versioning)
- [ ] `README.md` test count is accurate
  ```bash
  python3 -m pytest --collect-only -q 2>&1 | tail -2
  ```
- [ ] Example datasets in `data/examples/` run cleanly end-to-end
  ```bash
  python3 python/run_demo.py
  python3 python/run_cleaner.py \
    --input data/examples/dirty_orders.csv \
    --rules config/example_business_cleaning_rules.yaml \
    --dry-run
  ```
- [ ] `python3 python/doctor.py` reports no errors
- [ ] Docs are up to date: `docs/cleaning_rules_reference.md`, `docs/cleaning_execution.md`
- [ ] Roadmap (`docs/roadmap.md`) updated — completed items moved to the correct stage

---

## Release

- [ ] Tag the release: `git tag -a v0.X.0 -m "Release v0.X.0"`
- [ ] Push tag: `git push origin v0.X.0`
- [ ] Create GitHub release from the tag
  - Title: `v0.X.0 — [short description]`
  - Body: paste the relevant section from `CHANGELOG.md`
- [ ] Verify GitHub Actions CI passes on the release tag

---

## Post-release

- [ ] Add a new `[Unreleased]` section to `CHANGELOG.md`
- [ ] Update `[Unreleased]` compare link at the bottom of `CHANGELOG.md`
- [ ] Close any GitHub milestone for this release

---

## Suggested release titles

| Version | Title |
|---|---|
| v0.1.0 | Initial analyst workflow |
| v0.2.0 | Auditable cleaning and validation |
| v0.3.0 | Business-impact scorecards |
| v0.4.0 | R cleaning executor and framework exports |

← [README](../README.md) · [Roadmap](roadmap.md) · [Development](development.md)
