"""
toolkit
-------
Shared internal package for the data-cleaning-toolkit.

Provides:
  config          — reporter config + cleaning rules config
  io              — read/write tabular files
  type_detection  — infer semantic variable types
  profiling       — descriptive statistics, warnings, decision prompts
  report_writer   — render profiling output to markdown / HTML
  cleaning_actions— 14 cleaning action functions
  cleaning        — run_cleaning_pipeline() orchestrator
  validation      — schema checks + post-cleaning validation
  audit           — before/after dataset snapshots
  log_writer      — markdown cleaning log + run manifest
  example_datasets— load built-in example DataFrames
  utils           — shared helpers (abort, safety checks, etc.)
"""
