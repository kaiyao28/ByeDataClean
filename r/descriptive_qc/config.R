# config.R
# ─────────────────────────────────────────────────────────────────────────────
# Load and merge reporter configuration from a YAML file + CLI args.
# ─────────────────────────────────────────────────────────────────────────────

library(yaml)

DEFAULTS <- list(
  input_path         = NULL,
  example_dataset    = NULL,
  output_dir         = "reports/descriptive_summary",
  report_basename    = "descriptive_qc_report",
  columns            = NULL,
  id_cols            = NULL,
  mode               = "quick",
  type_overrides     = list(),
  date_columns       = character(0),
  schema_path        = NULL,
  thresholds = list(
    high_missingness       = 0.20,
    very_high_missingness  = 0.50,
    imbalance_cutoff       = 0.95,
    high_cardinality_cutoff= 50,
    rare_category_cutoff   = 0.01
  ),
  privacy = list(
    suppress_id_values          = TRUE,
    suppress_free_text_examples = TRUE,
    max_category_levels_shown   = 20
  )
)

load_config <- function(config_path = NULL) {
  cfg <- DEFAULTS
  if (!is.null(config_path)) {
    if (!file.exists(config_path)) stop(paste("Config file not found:", config_path))
    user_cfg <- yaml::read_yaml(config_path)
    # Shallow merge (top-level keys; nested lists from DEFAULTS are kept if absent)
    for (k in names(user_cfg)) {
      cfg[[k]] <- user_cfg[[k]]
    }
  }
  cfg
}

apply_cli_overrides <- function(cfg, cli_args) {
  mapping <- list(
    input            = "input_path",
    example_dataset  = "example_dataset",
    output_dir       = "output_dir",
    mode             = "mode"
  )
  for (cli_key in names(mapping)) {
    val <- cli_args[[cli_key]]
    if (!is.null(val) && val != "") cfg[[mapping[[cli_key]]]] <- val
  }
  if (!is.null(cli_args$columns) && cli_args$columns != "")
    cfg$columns <- strsplit(cli_args$columns, ",")[[1]]
  if (!is.null(cli_args$id_cols) && cli_args$id_cols != "")
    cfg$id_cols <- strsplit(cli_args$id_cols, ",")[[1]]
  cfg
}
