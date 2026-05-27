# utils.R
# ─────────────────────────────────────────────────────────────────────────────
# Shared helpers.
# ─────────────────────────────────────────────────────────────────────────────

pkg_available <- function(pkg) requireNamespace(pkg, quietly = TRUE)

check_optional_packages <- function(...) {
  pkgs <- c(...)
  status <- setNames(sapply(pkgs, pkg_available), pkgs)
  for (pkg in names(status)) {
    if (!status[[pkg]])
      message("[INFO] Optional package '", pkg, "' is not installed. Some features will be skipped.")
  }
  invisible(status)
}
