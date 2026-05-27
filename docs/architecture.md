# Architecture

## Repository structure

```
.
├── python/
│   ├── run_reporter.py             ← QC reporter entry point
│   ├── run_cleaner.py              ← cleaning executor entry point
│   └── toolkit/                   ← shared internal package
│       ├── config.py              ← reporter + cleaner config, DEFAULTS, rule loading
│       ├── io.py                  ← read_file / write_file (CSV, TSV, Excel, Parquet)
│       ├── type_detection.py      ← infer_types (continuous, binary, categorical, …)
│       ├── profiling.py           ← dataset stats, warnings, decision prompts
│       ├── report_writer.py       ← build_quick_report / write_quick_report
│       ├── cleaning_actions.py    ← 14 action functions with dry_run support
│       ├── cleaning.py            ← run_cleaning_pipeline orchestrator
│       ├── validation.py          ← schema checks (reporter) + post-clean validation
│       ├── audit.py               ← before/after snapshots
│       ├── log_writer.py          ← cleaning log, validation report, run manifest
│       ├── flowchart.py           ← Mermaid flowchart generator
│       ├── example_datasets.py    ← penguins / tips / iris loaders
│       └── utils.py               ← safety_check_output, warn, abort, print_banner
├── r/
│   ├── run_reporter.R              ← R reporter entry point
│   └── descriptive_qc/             ← R modules (skimr, janitor, DataExplorer)
├── sql/
│   ├── README.md                   ← how to use the cookbook
│   ├── inspection_cookbook/        ← 9 numbered SQL query templates
│   ├── dialect_notes/              ← DuckDB, PostgreSQL, BigQuery, SQLite
│   └── dbt_and_soda_notes.md
├── config/
│   ├── reporter_config.example.yaml   ← reporter config (copy and edit)
│   ├── schema.example.yaml            ← optional schema validation
│   ├── cleaning_rules.example.yaml    ← cleaning rules (copy and edit)
│   ├── category_mapping.example.yaml  ← category label mappings
│   ├── missing_codes.example.yaml     ← sentinel values to convert to NULL
│   └── cleaning_profiles/             ← pre-built rules for common analyses
│       ├── descriptive_analysis.yaml
│       ├── regression_analysis.yaml
│       ├── machine_learning.yaml
│       └── longitudinal_analysis.yaml
├── data/
│   ├── raw/                        ← put your input files here (git-ignored)
│   ├── interim/                    ← intermediate working files (git-ignored)
│   └── processed/                  ← cleaned output files (git-ignored)
├── reports/
│   ├── descriptive_summary/        ← markdown QC reports (git-ignored)
│   ├── full_profiles/              ← HTML profiles (git-ignored)
│   ├── cleaning_logs/              ← timestamped cleaning logs + run manifests (git-ignored)
│   └── validation_reports/         ← timestamped validation reports (git-ignored)
├── docs/
│   ├── cleaning_decision_guides/   ← 9 analyst guides + decision matrix
│   ├── templates/                  ← cleaning decision log template
│   ├── architecture.md             ← this file
│   ├── installation.md             ← detailed install guide
│   ├── usage.md                    ← extended usage examples
│   ├── reporter_reference.md       ← full reporter CLI and config reference
│   ├── cleaning_execution.md       ← full cleaner CLI reference
│   ├── cleaning_rules_reference.md ← all 14 actions with YAML examples
│   ├── before_after_validation.md  ← how to read snapshots and validation
│   ├── troubleshooting.md          ← common errors and fixes
│   ├── development.md              ← test suite, adding actions/checks
│   ├── roadmap.md                  ← stages and planned features
│   ├── package_comparison.md       ← when to use GX, Pandera, dbt, Soda
│   ├── sql_workflow.md             ← SQL cookbook usage
│   └── design.md                  ← design principles
├── tests/
│   ├── conftest.py                 ← adds python/ to sys.path
│   ├── test_cleaner_actions.py     ← 26 unit tests for action functions
│   ├── test_cleaner_smoke.py       ← 22 integration tests for the pipeline
│   ├── test_config_validation.py   ← 8 tests for config loading
│   ├── test_flowchart.py           ← 32 tests for Mermaid generation
│   ├── test_full_loop.py           ← 14 end-to-end loop tests
│   └── test_reporter_smoke.py      ← 15 tests for the reporter
├── README.md
├── pyproject.toml
├── requirements.txt
├── .gitignore
└── local/                          ← dev-only scripts (git-ignored)
```

---

## Data flow

```
run_reporter.py
  └── toolkit/io.py               read_file()
  └── toolkit/type_detection.py   infer_types()
  └── toolkit/profiling.py        dataset_overview(), missingness_summary(),
                                   duplication_summary(), continuous_summary(),
                                   binary_summary(), categorical_summary(),
                                   date_summary(), collect_all_warnings(),
                                   collect_all_prompts()
  └── toolkit/validation.py       run_schema_checks()   (if --schema)
  └── toolkit/report_writer.py    build_quick_report(), write_quick_report()

run_cleaner.py
  └── toolkit/io.py               read_file(), write_file()
  └── toolkit/config.py           load_rules(), validate_rules(),
                                   has_destructive_rules()
  └── toolkit/cleaning.py         run_cleaning_pipeline()
      ├── toolkit/audit.py           snapshot()
      ├── toolkit/cleaning_actions.py  apply_action() → action_*()
      ├── toolkit/validation.py      run_validation()
      ├── toolkit/log_writer.py      build_cleaning_log(), build_run_manifest(),
      │                               build_validation_report(), write_log(),
      │                               write_manifest()
      └── toolkit/flowchart.py       build_mermaid_flowchart(),
                                      write_flowchart_files()  (if --flowchart)
```

---

## Design principles

1. **No automatic cleaning.** Every cleaning step is declared explicitly in a YAML rules file.
2. **Raw data is immutable.** `safety_check_output()` aborts if input and output resolve to the same path.
3. **Dry-run first.** All actions support `dry_run=True`, which counts changes without writing.
4. **Every change is audited.** Cleaning log + run manifest (YAML with git commit hash) written after every run.
5. **Decisions are documented in code.** `decision_status` and `rationale` fields are logged verbatim.
6. **No mandatory external dependencies beyond pandas/numpy/pyyaml.** Optional packages enhance output but are never required.

See [`docs/design.md`](design.md) for full design rationale.

---

← [README](../README.md) · [Development](development.md) · [Roadmap](roadmap.md)
