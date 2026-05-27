#!/usr/bin/env Rscript
# run_reporter.R
# ─────────────────────────────────────────────────────────────────────────────
# Entry point for the R descriptive QC reporter.
#
# Usage:
#   Rscript r/run_reporter.R --example-dataset iris
#   Rscript r/run_reporter.R --example-dataset mtcars
#   Rscript r/run_reporter.R --example-dataset penguins
#   Rscript r/run_reporter.R --input data/raw/my_data.csv
#   Rscript r/run_reporter.R --input data/raw/my_data.csv --mode both
#   Rscript r/run_reporter.R --config config/reporter_config.example.yaml
# ─────────────────────────────────────────────────────────────────────────────

# Source modules relative to the repo root
repo_root <- normalizePath(file.path(dirname(sys.frame(1)$ofile), ".."),
                           mustWork = FALSE)
module_dir <- file.path(repo_root, "r", "descriptive_qc")

source(file.path(module_dir, "utils.R"))
source(file.path(module_dir, "config.R"))
source(file.path(module_dir, "io.R"))
source(file.path(module_dir, "example_datasets.R"))
source(file.path(module_dir, "profile.R"))
source(file.path(module_dir, "validation.R"))
source(file.path(module_dir, "report_writer.R"))

# ── Parse CLI arguments ───────────────────────────────────────────────────────
args <- commandArgs(trailingOnly = TRUE)

parse_args <- function(args) {
  result <- list(input = NULL, example_dataset = NULL, config = NULL,
                 columns = NULL, id_cols = NULL, mode = NULL,
                 output_dir = NULL, schema = NULL)
  i <- 1
  while (i <= length(args)) {
    flag <- args[i]
    val  <- if (i < length(args)) args[i + 1] else NULL

    if (flag == "--input")            { result$input           <- val; i <- i + 2 }
    else if (flag == "--example-dataset") { result$example_dataset <- val; i <- i + 2 }
    else if (flag == "--config")      { result$config          <- val; i <- i + 2 }
    else if (flag == "--columns")     { result$columns         <- val; i <- i + 2 }
    else if (flag == "--id-cols")     { result$id_cols         <- val; i <- i + 2 }
    else if (flag == "--mode")        { result$mode            <- val; i <- i + 2 }
    else if (flag == "--output-dir")  { result$output_dir      <- val; i <- i + 2 }
    else if (flag == "--schema")      { result$schema          <- val; i <- i + 2 }
    else {
      message("[WARNING] Unknown flag: ", flag)
      i <- i + 1
    }
  }
  result
}

cli_args <- parse_args(args)

# ── Load and merge config ─────────────────────────────────────────────────────
cfg <- load_config(cli_args$config)
cfg <- apply_cli_overrides(cfg, cli_args)

# Validate
if (is.null(cfg$input_path) && is.null(cfg$example_dataset)) {
  stop("Provide either --input <path> or --example-dataset <name>.")
}

# ── Optional package check ────────────────────────────────────────────────────
check_optional_packages("skimr", "DataExplorer", "palmerpenguins", "readr", "dplyr", "janitor")

# ── Load data ─────────────────────────────────────────────────────────────────
if (!is.null(cfg$example_dataset)) {
  df           <- load_example_dataset(cfg$example_dataset)
  source_label <- paste0("example:", cfg$example_dataset)
} else {
  df           <- read_file(cfg$input_path)
  source_label <- cfg$input_path
}

# Column selection
df <- select_columns(df, cfg$columns)

# janitor: clean column names (optional)
if (requireNamespace("janitor", quietly = TRUE)) {
  df <- janitor::clean_names(df)
  message("[INFO] Column names cleaned via janitor::clean_names().")
}

# ── Profile ───────────────────────────────────────────────────────────────────
overview    <- dataset_overview(df)
miss        <- missingness_summary(df, cfg$thresholds)
dups        <- duplication_summary(df, cfg$id_cols)
skim_result <- run_skim(df)

# ── Schema checks ─────────────────────────────────────────────────────────────
schema_issues <- NULL
if (!is.null(cfg$schema_path)) {
  tryCatch({
    schema        <- load_schema(cfg$schema_path)
    schema_issues <- run_schema_checks(df, schema)
  }, error = function(e) {
    message("[WARNING] Schema check failed: ", e$message)
  })
}

# ── Render and write ──────────────────────────────────────────────────────────
mode <- cfg$mode

if (mode %in% c("quick", "both")) {
  report_str <- build_quick_report(cfg, source_label, overview, miss, dups,
                                   skim_result, schema_issues)
  cat(report_str, "\n")
  out_path   <- write_quick_report(report_str, cfg)
  message("\n✓ Quick report saved → ", out_path)
}

if (mode %in% c("full", "both")) {
  run_full_profile(df, cfg)
}
