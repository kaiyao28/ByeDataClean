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

## Stage 3 — complete

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
- 128 pytest tests (unit + integration + flowchart + full-loop)

## Stage 4 — planned

- Full HTML profiling mode via ydata-profiling (Python)
- Full HTML profiling mode via DataExplorer (R)
- Complete R cleaning executor (`run_cleaner.R`)
- Pandera schema validation integration
- pointblank examples (R)
- dbt test generation templates
- Soda Core check templates

## Deferred (not in scope for V1)

- Fuzzy/phonetic category matching
- Automated imputation
- ML preprocessing pipeline
- Web UI or Streamlit dashboard
- Enterprise lineage tracking (OpenLineage/Marquez)

---

← [README](../README.md) · [Development](development.md)
