# io.R
# ─────────────────────────────────────────────────────────────────────────────
# Read tabular data from disk.
# ─────────────────────────────────────────────────────────────────────────────

read_file <- function(path) {
  if (!file.exists(path)) stop(paste("Input file not found:", path))

  ext <- tolower(tools::file_ext(path))

  if (ext %in% c("csv", "txt")) {
    readr::read_csv(path, show_col_types = FALSE)
  } else if (ext == "tsv") {
    readr::read_tsv(path, show_col_types = FALSE)
  } else if (ext %in% c("xls", "xlsx")) {
    if (!requireNamespace("readxl", quietly = TRUE)) {
      stop("Package 'readxl' is required for Excel files. Install with: install.packages('readxl')")
    }
    readxl::read_excel(path)
  } else {
    message("[io] Unrecognised extension '", ext, "'; attempting CSV read.")
    readr::read_csv(path, show_col_types = FALSE)
  }
}

select_columns <- function(df, columns) {
  if (is.null(columns)) return(df)
  missing_cols <- setdiff(columns, names(df))
  if (length(missing_cols) > 0) {
    stop(paste(
      "Requested columns not found:", paste(missing_cols, collapse = ", "),
      "\nAvailable:", paste(names(df), collapse = ", ")
    ))
  }
  df[, columns, drop = FALSE]
}
