# Roadmap

## Stage 1 — complete

- Python quick reporter (markdown summary)
- Python example dataset loader (penguins, tips, iris)
- SQL inspection cookbook (9 files, 4 dialect notes)
- Config and schema files with examples
- pytest smoke tests

## Stage 2 — complete

- Cleaning decision guides (9 guides + decision log template)
- Cleaning decision prompts section in the QC report
- Config templates: cleaning rules, category mappings, missing codes
- 4 analysis-specific cleaning profiles (descriptive, regression, ML, longitudinal)

## Stage 3 — complete (v0.2.0)

- Config-driven Python cleaning executor (`run_cleaner.py`)
- 14 cleaning actions with dry-run support (including `create_missingness_flags`)
- `decision_status` + `rationale` fields in every cleaning rule — logged verbatim
- Machine-readable run manifest YAML (git commit, Python version, row/column counts)
- `--confirm-destructive` CLI guard for row/column drops
- Global `safety:` block in rules YAML
- Before/after dataset snapshots and validation checks
- Timestamped cleaning log (with embedded Mermaid flowchart), run manifest, and validation report
- `--flowchart` flag: generates `.mmd` and `.md` Mermaid flow diagrams (no extra packages required)
- Step Impact Summary table always included in cleaning log
- Unified `python/toolkit/` internal package
- 130 pytest tests (unit + integration + flowchart + full-loop)
- `--mode full` / `--mode both`: HTML profile via ydata-profiling (requires `pip install ydata-profiling`)
- Validation fail-fast mode (`validation: fail_on_error: true`)
- Manager-friendly cleaning summary generated alongside every cleaning log

## Stage 3b — complete (v0.3.0)

- Business-impact case study: e-commerce orders dataset (`data/examples/dirty_orders.csv`)
- Per-rule business metadata fields: `severity`, `business_metric`, `owner`, `action_required`, `stakeholder_note`
- Config validation for invalid `severity` and `action_required` values
- Business metadata included in cleaning log and manager summary (grouped by severity)
- Data-quality scorecard (`python/toolkit/scorecard.py`): PASS / WARNING / BLOCKER + recommended-use grid
- `--scorecard` CLI flag → `reports/scorecards/`
- Business metric impact calculator (`python/toolkit/business_impact.py` + `python/run_business_impact.py`)
- Decision memo generator (`python/toolkit/decision_memo.py`) + `--decision-memo` CLI flag → `reports/manager_summaries/`
- Decision memo static template (`docs/templates/decision_memo_template.md`)
- dbt / Pandera / Soda export starter templates (`python/export_quality_checks.py`)
- GitHub issue templates and pull request template
- CHANGELOG.md and release checklist
- 204 pytest tests

## Stage 4 — planned

- Full HTML profiling mode via DataExplorer (R)
- Complete R cleaning executor (`run_cleaner.R`)
- Full Pandera integration (round-trip schema sync)
- pointblank examples (R)
- Full dbt test generation (beyond starter templates)
- Full Soda Core integration

## Deferred (not in scope for V1)

- Fuzzy/phonetic category matching
- Automated imputation
- ML preprocessing pipeline
- Web UI or Streamlit dashboard
- Enterprise lineage tracking (OpenLineage/Marquez)

---

← [README](../README.md) · [Development](development.md)
