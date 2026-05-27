# profile.R
# ─────────────────────────────────────────────────────────────────────────────
# Compute descriptive statistics.  Uses skimr::skim() as the core engine.
# ─────────────────────────────────────────────────────────────────────────────

library(dplyr)

dataset_overview <- function(df) {
  list(
    n_rows   = nrow(df),
    n_cols   = ncol(df),
    columns  = names(df),
    mem_kb   = round(object.size(df) / 1024, 1)
  )
}

run_skim <- function(df) {
  if (!requireNamespace("skimr", quietly = TRUE)) {
    message("[profile] 'skimr' not installed — skipping skim summary.\n",
            "  Install with: install.packages('skimr')")
    return(NULL)
  }
  skimr::skim(df)
}

missingness_summary <- function(df, thresholds) {
  high      <- thresholds$high_missingness
  very_high <- thresholds$very_high_missingness
  n         <- nrow(df)

  miss_pct <- sapply(df, function(col) sum(is.na(col)) / n)

  list(
    fully_missing    = names(miss_pct[miss_pct == 1]),
    very_high_missing= names(miss_pct[miss_pct > very_high & miss_pct < 1]),
    high_missing     = names(miss_pct[miss_pct > high & miss_pct <= very_high]),
    top_missing      = sort(miss_pct[miss_pct > 0], decreasing = TRUE)[1:min(10, sum(miss_pct > 0))]
  )
}

duplication_summary <- function(df, id_cols = NULL) {
  n_exact <- sum(duplicated(df))
  result <- list(exact_duplicate_rows = n_exact)
  if (!is.null(id_cols)) {
    valid <- intersect(id_cols, names(df))
    if (length(valid) > 0) {
      n_dup_ids <- sum(duplicated(df[, valid, drop = FALSE], fromLast = FALSE) |
                       duplicated(df[, valid, drop = FALSE], fromLast = TRUE))
      result$duplicate_id_rows    <- n_dup_ids
      result$id_cols_checked      <- valid
    }
  }
  result
}
