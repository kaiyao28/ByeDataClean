# Development

## Running tests

```bash
python -m pytest
```

With verbose output:

```bash
python -m pytest tests/ -v
```

One specific file:

```bash
python -m pytest tests/test_flowchart.py -v
```

---

## Test suite

**128 tests** across five files — all pass in under 2 seconds on a laptop.

| File | What it tests | Tests |
|---|---|---|
| `tests/test_cleaner_actions.py` | Each of the 14 cleaning action functions: unit tests with and without dry-run | 26 |
| `tests/test_cleaner_smoke.py` | Cleaning pipeline end-to-end: log sections, dry-run, manifest, safety checks | 22 |
| `tests/test_flowchart.py` | Flowchart module: node labels, Mermaid syntax, CSS classes, file I/O, pipeline integration | 32 |
| `tests/test_full_loop.py` | Full analyst loop: profile → clean → re-profile → validate, flowchart, byte-exact raw file check | 14 |
| `tests/test_reporter_smoke.py` | QC reporter: report output, type inference, and decision prompts | 15 |
| `tests/test_config_validation.py` | Config loading, defaults, and validation errors | 8 |

### Test design principles

- All tests build DataFrames in-memory or write only to pytest's `tmp_path`.
- No external files are read from disk by any test.
- No optional packages (`seaborn`, `ydata-profiling`, etc.) are required.
- `conftest.py` at the repo root adds `python/` to `sys.path`, so `toolkit.*` imports work.

---

## Repository layout (Python)

```
python/
├── run_reporter.py          ← QC reporter entry point
├── run_cleaner.py           ← cleaning executor entry point
└── toolkit/                 ← shared internal package
    ├── __init__.py
    ├── config.py            ← DEFAULTS, load_config, load_rules, validate_rules,
    │                           has_destructive_rules, SUPPORTED_ACTIONS
    ├── io.py                ← read_file, write_file, default_output_path
    ├── type_detection.py    ← infer_types
    ├── profiling.py         ← dataset_overview, missingness_summary,
    │                           duplication_summary, continuous_summary,
    │                           binary_summary, categorical_summary, date_summary,
    │                           collect_all_warnings, collect_all_prompts,
    │                           DecisionPrompt
    ├── report_writer.py     ← build_quick_report, write_quick_report
    ├── cleaning_actions.py  ← 14 action functions + apply_action dispatcher
    ├── cleaning.py          ← run_cleaning_pipeline
    ├── validation.py        ← run_schema_checks (reporter), run_validation (cleaner),
    │                           ValidationResult
    ├── audit.py             ← snapshot, before_after_summary
    ├── log_writer.py        ← build_cleaning_log, build_validation_report,
    │                           build_run_manifest, write_log, write_manifest
    ├── flowchart.py         ← build_mermaid_flowchart, write_flowchart_files
    ├── example_datasets.py  ← load_example_dataset
    └── utils.py             ← safety_check_output, check_optional_packages,
                                warn, info, abort, print_banner
```

---

## Adding a new cleaning action

1. Add a function `action_<name>(df, rule, dry_run=False) -> (pd.DataFrame, dict)` in `toolkit/cleaning_actions.py`.
2. The returned dict must have: `rows_before`, `rows_after`, `rows_delta`, `cells_changed`, `warnings`, `details`.
3. Add `"<name>"` to `SUPPORTED_ACTIONS` in `toolkit/config.py`.
4. Add `"<name>": action_<name>` to `ACTION_MAP` in `toolkit/cleaning_actions.py`.
5. Add unit tests to `tests/test_cleaner_actions.py` covering: normal run, dry_run, and edge cases.
6. Document the action in `docs/cleaning_rules_reference.md`.

---

## Adding a new reporter check

1. Add a `check_*` function in `toolkit/profiling.py` returning `list[str]` (warning strings).
2. Call it from `collect_all_warnings(...)`.
3. Add a `prompts_from_*` function returning `list[DecisionPrompt]` if it generates analyst prompts.
4. Call it from `collect_all_prompts(...)`.
5. Add tests to `tests/test_reporter_smoke.py`.

---

## Back to main docs

← [README](../README.md) · [Architecture](architecture.md) · [Roadmap](roadmap.md)
