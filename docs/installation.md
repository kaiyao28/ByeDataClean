# Installation

## Python setup

**macOS / Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Windows (PowerShell):**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

This installs the core dependencies: `pandas`, `numpy`, `pyyaml`, and `pytest`.

### Optional packages

Install only what you need:

```bash
pip install seaborn          # required for --example-dataset penguins / tips
pip install scikit-learn     # alternative source for --example-dataset iris
pip install skimpy           # adds a richer console summary table
pip install ydata-profiling  # required for --mode full or --mode both (HTML report)
```

The reporter will tell you clearly if an optional package is missing — it will not crash; it continues with the core summary.

### VS Code Python interpreter

If running from VS Code, make sure the interpreter is set to the `.venv` environment:

1. Open the Command Palette (`Cmd/Ctrl + Shift + P`)
2. Select **Python: Select Interpreter**
3. Choose `.venv/bin/python`

---

## R setup

Install required packages from CRAN:

```r
install.packages(c("readr", "dplyr", "janitor", "skimr", "yaml"))
```

Optional packages:

```r
install.packages("palmerpenguins")  # for --example-dataset penguins
install.packages("DataExplorer")    # for --mode full or --mode both (HTML report)
```

---

## SQL setup

No installation required. The SQL files in `sql/inspection_cookbook/` are plain text templates. Open them in any SQL client, replace the `{{ placeholder }}` tokens, and run.

Supported clients: DBeaver, DataGrip, `psql`, DuckDB CLI, any JDBC/ODBC client.

---

## Requirements summary

| Tool | Core requirement | Optional enhancement |
|---|---|---|
| Python | `pandas`, `numpy`, `pyyaml` | `seaborn`, `ydata-profiling`, `skimpy` |
| R | `readr`, `dplyr`, `janitor`, `skimr`, `yaml` | `palmerpenguins`, `DataExplorer` |
| SQL | Nothing | Any SQL client |

---

## Back to main docs

← [README](../README.md) · [Usage guide](usage.md) · [Reporter reference](reporter_reference.md)
