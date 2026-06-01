# Glossary

Plain-language definitions for terms used in ByeDataClean reports and documentation.

---

**audit log**
A timestamped record of every cleaning step applied to a dataset, including what changed, how many rows or cells were affected, and the analyst's stated rationale. Saved automatically after every cleaning run. See: cleaning log.

**cleaned data**
A copy of the raw dataset after cleaning rules have been applied. Raw data is never overwritten — cleaned data is always written to a separate file (usually `data/processed/`).

**cleaning log**
The markdown file written after each cleaning run. Contains: run metadata, a step-by-step summary of what changed, validation results, and a before/after snapshot. Saved to `reports/cleaning_logs/`.

**config file**
A YAML file that controls the behaviour of a script without requiring code changes. In ByeDataClean, config files describe cleaning rules, reporter settings, or schema expectations.

**destructive action**
A cleaning step that removes rows or columns. Examples: `remove_exact_duplicates`, `drop_columns`, `filter_rows_explicit`. Destructive actions require explicit opt-in in both the rules file and the CLI command.

**dry run**
A mode that simulates every cleaning step and counts what would change, without writing any output to `data/processed/`. Always run dry first before applying cleaning.

**duplicate ID**
Two or more rows sharing the same identifier (e.g. same `participant_id`). This may indicate a data-entry error, a repeated measure, or a merged dataset. Different from a duplicate row.

**duplicate row**
Two or more rows that are identical on every column. Usually an accidental double-export. Can be removed safely once confirmed.

**flowchart**
A visual diagram of the cleaning pipeline, showing each step as a node with counts (rows changed, cells changed, warnings). Generated as a Mermaid diagram, saved alongside the cleaning log.

**high cardinality**
A categorical column with many distinct values (e.g. free-text notes, postal codes). High-cardinality columns are flagged in the QC report because they are usually not suitable for direct analysis and may contain sensitive data.

**IQR (interquartile range)**
The distance between the 25th and 75th percentiles of a numeric column. Used by the `flag_outliers_iqr` action to detect potential outliers: values that fall more than 1.5 × IQR below the 25th percentile or above the 75th percentile are flagged.

**missing value**
A cell with no recorded value. In ByeDataClean, missing values are represented as `NaN` (Not a Number) in pandas. Missing-data codes like `"NA"`, `"Unknown"`, or `-9` are converted to `NaN` by the `replace_missing_codes` action.

**missingness**
The proportion of values in a column (or dataset) that are missing. A column with 20% missingness has 1 in 5 values absent. The reporter flags columns above configurable thresholds (default: 20% and 50%).

**outlier**
A value that is unusually far from the rest of the distribution. In ByeDataClean, "outlier" specifically refers to IQR-based outliers detected by `flag_outliers_iqr`. Outliers are flagged by default — not removed. Whether to remove or keep an outlier depends on whether it represents a data-entry error or a genuine extreme value.

**rare category**
A category that appears in fewer than a configurable proportion of rows (default: 1%). Rare categories are flagged because they may cause issues in statistical models and may represent data-entry errors.

**raw data**
The original, unmodified dataset. In ByeDataClean, raw data is always kept in `data/raw/` and is never overwritten by the cleaning pipeline.

**run manifest**
A machine-readable YAML file written alongside each cleaning log. Contains: timestamp, input/output file paths, rules file path, git commit hash, Python version, and row/column counts before and after cleaning. Useful for reproducibility audits.

**schema**
A formal description of the expected structure of a dataset: which columns are required, what types they should be, what values are allowed, and what ranges are valid. In ByeDataClean, schemas are defined in `config/schema.example.yaml` and used by both the reporter and the cleaning validator.

**validation**
After cleaning, a set of checks run against the cleaned dataset to confirm it meets expectations. Checks include: required columns present, unique key constraints, accepted values, and numeric ranges. Results are saved to `reports/validation_reports/`.

**YAML**
A plain-text format for writing structured data using indentation instead of brackets or commas. ByeDataClean uses YAML for all config and rules files. See [docs/yaml_for_beginners.md](yaml_for_beginners.md) for an introduction.

---

← [README](../README.md) · [I have a CSV](i_have_a_csv_what_do_i_do.md) · [Troubleshooting](troubleshooting.md)
