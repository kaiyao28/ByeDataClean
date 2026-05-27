# validation.R
# ─────────────────────────────────────────────────────────────────────────────
# Schema-based validation checks.
# ─────────────────────────────────────────────────────────────────────────────

library(yaml)

load_schema <- function(schema_path) {
  if (!file.exists(schema_path)) stop(paste("Schema file not found:", schema_path))
  yaml::read_yaml(schema_path)
}

run_schema_checks <- function(df, schema) {
  col_schema <- schema$columns
  issues <- list(
    missing_required       = character(0),
    allowed_value_violations = character(0),
    range_violations       = character(0),
    uniqueness_violations  = character(0)
  )

  df_cols <- names(df)

  for (col in names(col_schema)) {
    spec <- col_schema[[col]]

    # Required columns
    if (isTRUE(spec$required) && !(col %in% df_cols)) {
      issues$missing_required <- c(issues$missing_required,
        paste0("Required column '", col, "' is missing."))
      next
    }
    if (!(col %in% df_cols)) next

    vals <- df[[col]]

    # Allowed values
    if (!is.null(spec$allowed_values)) {
      bad <- vals[!is.na(vals) & !(vals %in% spec$allowed_values)]
      if (length(bad) > 0) {
        issues$allowed_value_violations <- c(issues$allowed_value_violations,
          paste0("'", col, "': ", length(bad), " disallowed value(s). ",
                 "Examples: ", paste(head(unique(bad), 5), collapse = ", ")))
      }
    }

    # Numeric range
    if (!is.null(spec$min)) {
      n_below <- sum(!is.na(vals) & vals < spec$min)
      if (n_below > 0)
        issues$range_violations <- c(issues$range_violations,
          paste0("'", col, "': ", n_below, " value(s) below min (", spec$min, ")."))
    }
    if (!is.null(spec$max)) {
      n_above <- sum(!is.na(vals) & vals > spec$max)
      if (n_above > 0)
        issues$range_violations <- c(issues$range_violations,
          paste0("'", col, "': ", n_above, " value(s) above max (", spec$max, ")."))
    }

    # Uniqueness
    if (isTRUE(spec$unique) || identical(spec$role, "id")) {
      non_null <- vals[!is.na(vals)]
      n_dup <- sum(duplicated(non_null))
      if (n_dup > 0)
        issues$uniqueness_violations <- c(issues$uniqueness_violations,
          paste0("'", col, "': ", n_dup, " duplicate non-null value(s)."))
    }
  }

  issues
}
