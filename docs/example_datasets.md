# Example Datasets

Built-in example datasets let you run the reporter immediately without
needing your own data.

---

## Python example datasets

### penguins

- **Source**: `seaborn.load_dataset("penguins")`
- **Requires**: `pip install seaborn` (optional)
- **Coverage**: Continuous (bill length/depth, flipper length, body mass), binary (sex), categorical (species, island)
- **Useful for**: Testing continuous + binary + categorical + missingness all at once

```bash
python python/run_reporter.py --example-dataset penguins
```

### tips

- **Source**: `seaborn.load_dataset("tips")`
- **Requires**: `pip install seaborn` (optional)
- **Coverage**: Continuous (total bill, tip), binary (sex, smoker), categorical (day, time), ordinal-ish (size)

```bash
python python/run_reporter.py --example-dataset tips
```

### iris

- **Source**: `sklearn.datasets.load_iris` (preferred) or `seaborn.load_dataset("iris")` (fallback)
- **Requires**: `pip install scikit-learn` or `pip install seaborn` (optional)
- **Coverage**: Continuous (sepal/petal measurements), categorical (species)

```bash
python python/run_reporter.py --example-dataset iris
```

> **Note**: seaborn caches datasets in `~/seaborn-data/` after the first download.
> Subsequent calls are offline.  If you have no internet access and no cache,
> the reporter will print a helpful message and exit.

---

## R example datasets

### iris

- **Source**: Base R `datasets::iris`
- **No install required**

```bash
Rscript r/run_reporter.R --example-dataset iris
```

### mtcars

- **Source**: Base R `datasets::mtcars`
- **No install required**

```bash
Rscript r/run_reporter.R --example-dataset mtcars
```

### penguins

- **Source**: `palmerpenguins::penguins`
- **Requires**: `install.packages("palmerpenguins")` (optional)
- **Fallback**: If `palmerpenguins` is not installed, `iris` is used instead with a helpful message.

```bash
Rscript r/run_reporter.R --example-dataset penguins
```
