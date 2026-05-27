# report_writer.R
# ─────────────────────────────────────────────────────────────────────────────
# Write the quick markdown report and optionally an HTML profile.
# ─────────────────────────────────────────────────────────────────────────────

build_quick_report <- function(cfg, source_label, overview, miss, dups,
                                skim_result, schema_issues) {
  lines <- character(0)
  add   <- function(...) lines <<- c(lines, paste0(...))

  add("# Descriptive QC Report\n")
  add("- **Timestamp:** ", format(Sys.time(), "%Y-%m-%d %H:%M:%S"))
  add("- **Input source:** ", source_label)
  add("- **Selected columns:** ", ifelse(is.null(cfg$columns), "all", paste(cfg$columns, collapse = ", ")))
  add("- **ID columns:** ", ifelse(is.null(cfg$id_cols), "none", paste(cfg$id_cols, collapse = ", ")))
  add("- **Report mode:** ", cfg$mode)
  add("")

  add("## Dataset Overview\n")
  add("- **Rows:** ", format(overview$n_rows, big.mark = ","))
  add("- **Columns:** ", overview$n_cols)
  add("- **Memory (KB):** ", overview$mem_kb)
  add("- **Columns:** ", paste(overview$columns, collapse = ", "))
  add("")

  add("## Missingness Summary\n")
  if (length(miss$fully_missing) > 0)
    add("- **Fully missing:** ", paste(miss$fully_missing, collapse = ", "))
  if (length(miss$very_high_missing) > 0)
    add("- **Very-high missingness (>50%):** ", paste(miss$very_high_missing, collapse = ", "))
  if (length(miss$high_missing) > 0)
    add("- **High missingness (>20%):** ", paste(miss$high_missing, collapse = ", "))
  if (length(miss$top_missing) > 0) {
    add("\n### Top missing columns (%)")
    for (col in names(miss$top_missing))
      add("- ", col, ": ", round(miss$top_missing[[col]] * 100, 1), "%")
  } else {
    add("No missing values detected.")
  }
  add("")

  add("## Duplication Summary\n")
  add("- **Exact duplicate rows:** ", dups$exact_duplicate_rows)
  if (!is.null(dups$duplicate_id_rows))
    add("- **Rows with duplicate ID (", paste(dups$id_cols_checked, collapse = ", "), "):** ", dups$duplicate_id_rows)
  add("")

  if (!is.null(skim_result)) {
    add("## skimr Summary\n")
    add("```")
    add(paste(capture.output(print(skim_result)), collapse = "\n"))
    add("```\n")
  }

  if (!is.null(schema_issues)) {
    add("## Schema Checks\n")
    any_issues <- FALSE
    for (issue_type in names(schema_issues)) {
      msgs <- schema_issues[[issue_type]]
      if (length(msgs) > 0) {
        any_issues <- TRUE
        add("### ", gsub("_", " ", issue_type))
        for (m in msgs) add("- ", m)
      }
    }
    if (!any_issues) add("✓ No schema violations detected.")
    add("")
  }

  paste(lines, collapse = "\n")
}

write_quick_report <- function(report_str, cfg) {
  out_dir  <- cfg$output_dir
  if (!dir.exists(out_dir)) dir.create(out_dir, recursive = TRUE)
  basename <- cfg$report_basename
  ts       <- format(Sys.time(), "%Y%m%d_%H%M%S")
  out_path <- file.path(out_dir, paste0(basename, "_", ts, ".md"))
  writeLines(report_str, out_path)
  out_path
}

run_full_profile <- function(df, cfg) {
  if (!requireNamespace("DataExplorer", quietly = TRUE)) {
    message("[report_writer] 'DataExplorer' not installed — skipping full HTML report.\n",
            "  Install with: install.packages('DataExplorer')")
    return(invisible(NULL))
  }
  out_dir  <- file.path(cfg$output_dir, "..", "full_profiles")
  if (!dir.exists(out_dir)) dir.create(out_dir, recursive = TRUE)
  ts       <- format(Sys.time(), "%Y%m%d_%H%M%S")
  out_path <- file.path(out_dir, paste0(cfg$report_basename, "_", ts, ".html"))
  message("[report_writer] Generating DataExplorer HTML report…")
  DataExplorer::create_report(df, output_file = basename(out_path),
                              output_dir = dirname(out_path))
  out_path
}
