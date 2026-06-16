# Changelog

All notable changes to ByeDataClean are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versions follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

---

## [0.3.0] — 2026-06-15

### Added
- Business-impact case study: `data/examples/dirty_orders.csv` and `config/example_business_cleaning_rules.yaml`
- E-commerce case study document: `docs/case_studies/ecommerce_revenue_quality.md`
- Per-rule business metadata fields: `severity`, `business_metric`, `owner`, `action_required`, `stakeholder_note`
- Config validation for `severity` and `action_required` (invalid values raise clear errors)
- Business metadata included in cleaning log Step Summary and Detailed Step Notes
- Manager summary now groups unresolved issues by severity
- Data-quality scorecard (`python/toolkit/scorecard.py`): PASS / WARNING / BLOCKER status with recommended-use grid
- `--scorecard` CLI flag for `run_cleaner.py` — writes to `reports/scorecards/`
- Business metric impact calculator (`python/toolkit/business_impact.py` and `python/run_business_impact.py`)
- Decision memo generator (`python/toolkit/decision_memo.py`) with `--decision-memo` CLI flag
- Decision memo template: `docs/templates/decision_memo_template.md`
- Export starter templates for dbt, Pandera and Soda Core (`python/export_quality_checks.py`)
- GitHub issue templates (bug, feature, cleaning action request) and PR template
- SQL inspection cookbook revamped: business-framing, Python/R parity table, dialect notes
- SQL e-commerce worked example (`sql/examples/ecommerce_orders_quality_checks.sql`): 12 checks including duplicate GMV overstatement, missingness rates, date validity, scorecard summary query
- `docs/example_outputs/` — browsable scorecard, decision memo, cleaning log excerpt, and flowchart from the e-commerce case study
- `Makefile` — `install`, `test`, `demo`, `demo-orders`, `lint`, `format`, `check` targets
- `pyproject.toml` — updated description, classifiers, and ruff config
- README restructured as lean landing page: "From messy data to trustworthy decisions" tagline, user-journey Mermaid, business impact table, output table, Python/R vs SQL comparison
- `docs/assets/README.md` — banner design specification and Canva/Figma prompt
- Who-this-is-for and limitations wording added (docs and README)
- 204 pytest tests (74 new since 0.2.0)

---

## [0.2.0] — 2024-12-01

### Added
- Config-driven Python cleaning executor (`run_cleaner.py`) with 14 cleaning actions
- `decision_status` and `rationale` fields in every cleaning rule — logged verbatim
- Machine-readable run manifest YAML (git commit, Python version, row/column counts)
- `--confirm-destructive` CLI guard for row/column drops
- Global `safety:` block in rules YAML
- Before/after dataset snapshots and validation checks (`required_columns`, `unique_keys`, `accepted_values`, `ranges`)
- Timestamped cleaning log with embedded Mermaid flowchart (`--flowchart`)
- Step Impact Summary table always included in cleaning log
- Manager-friendly cleaning summary generated alongside every cleaning log
- Validation fail-fast mode (`validation: fail_on_error: true`)
- Unified `python/toolkit/` internal package (14 modules)
- 130 pytest tests (unit + integration + flowchart + full-loop)
- `parse_dates` action (action #11): converts strings to datetime, coerces invalid dates to NaT
- `create_missingness_flags` action (action #14): adds binary flag columns for missing values
- Bundled dirty dataset (`data/examples/example_dirty_data.csv`) with 50 rows of realistic issues
- One-command demo (`python/run_demo.py`)
- Environment check script (`python/doctor.py`)
- GitHub Actions CI: Python 3.9, 3.10, 3.11, 3.12
- MIT License
- 9 documentation files under `docs/`

### Fixed
- `is_object_dtype` check missed `pd.StringDtype` on pandas 2.0+ (Python 3.11/3.12 CI failure)

---

## [0.1.0] — 2024-06-01

### Added
- Python quick reporter (`run_reporter.py`): markdown QC summary for CSV/TSV/Excel/Parquet
- Python example dataset loader (penguins, tips, iris)
- SQL inspection cookbook (`sql/inspection_cookbook/`): 9 numbered query templates
- Config and schema files with examples
- R reporter (`r/run_reporter.R`) using skimr and janitor
- Cleaning decision guides (9 guides + decision log template)
- Cleaning decision prompts in QC report
- Config templates: cleaning rules, category mappings, missing codes
- 4 analysis-specific cleaning profiles (descriptive, regression, ML, longitudinal)
- pytest smoke tests

---

[Unreleased]: https://github.com/kaiyao28/ByeDataClean/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/kaiyao28/ByeDataClean/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/kaiyao28/ByeDataClean/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/kaiyao28/ByeDataClean/releases/tag/v0.1.0
