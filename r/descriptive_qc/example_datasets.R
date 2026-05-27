# example_datasets.R
# ─────────────────────────────────────────────────────────────────────────────
# Load built-in public example datasets for R.
# ─────────────────────────────────────────────────────────────────────────────

load_example_dataset <- function(name) {
  name <- tolower(trimws(name))

  if (name == "iris") {
    message("[example_datasets] Loading 'iris' from base R datasets.")
    return(datasets::iris)
  }

  if (name == "mtcars") {
    message("[example_datasets] Loading 'mtcars' from base R datasets.")
    return(datasets::mtcars)
  }

  if (name == "penguins") {
    if (!requireNamespace("palmerpenguins", quietly = TRUE)) {
      message(
        "[example_datasets] 'palmerpenguins' is not installed.\n",
        "  Install with: install.packages('palmerpenguins')\n",
        "  Falling back to 'iris' instead."
      )
      return(datasets::iris)
    }
    message("[example_datasets] Loading 'penguins' from palmerpenguins.")
    return(palmerpenguins::penguins)
  }

  stop(paste0(
    "[example_datasets] Unknown dataset: '", name, "'.\n",
    "  Available: iris, mtcars, penguins\n",
    "  Use --input to load your own file instead."
  ))
}
