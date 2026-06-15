.PHONY: install test demo lint format check

install:
	pip install -e ".[dev]"

install-all:
	pip install -e ".[all]"

test:
	python3 -m pytest tests/ -q

test-verbose:
	python3 -m pytest tests/ -v

demo:
	python3 python/run_demo.py

demo-orders:
	python3 python/run_cleaner.py \
		--input data/examples/dirty_orders.csv \
		--rules config/example_business_cleaning_rules.yaml \
		--output data/processed/orders_clean.csv \
		--scorecard \
		--decision-memo \
		--flowchart \
		--dry-run

lint:
	python3 -m ruff check python/ tests/

format:
	python3 -m ruff format python/ tests/

check: lint test
