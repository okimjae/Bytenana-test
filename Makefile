.PHONY: help run test evals map db clean

help:
	@echo "========================================================"
	@echo " 🚀 Buda & Hays County Spatial Data Pipeline Shortcuts"
	@echo "========================================================"
	@echo "  make run    - Run full pipeline (Ingestion -> Spatial -> DB Sink -> Evals)"
	@echo "  make map    - Generate and open interactive web map in browser"
	@echo "  make test   - Run full automated test suite (17 assertions)"
	@echo "  make evals  - Run automated Evaluation Harness"
	@echo "  make db     - Inspect tables, rows, and agent loop audits in database"
	@echo "  make clean  - Clean temporary files and caches"
	@echo "========================================================"

run:
	.venv/bin/python run_pipeline.py

map:
	.venv/bin/python -m src.viz.generate_map

test:
	.venv/bin/pytest tests/ -v

evals:
	.venv/bin/python -m src.evals.eval_harness

db:
	.venv/bin/python -m src.db.inspect_db

clean:
	rm -rf __pycache__ .pytest_cache .coverage htmlcov map_preview.html
