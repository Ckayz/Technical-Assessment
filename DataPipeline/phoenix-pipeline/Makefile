.PHONY: help install run test clean format lint

help:  ## Show this help message
	@echo "Phoenix Pipeline - Makefile Commands"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install:  ## Install dependencies with uv
	uv pip install -e .

run:  ## Run the pipeline
	python -m phoenix_pipeline.main

test:  ## Run all tests
	python test_main.py
	python test_coingecko_logic.py
	python test_transform_enrich.py
	python test_io.py

clean:  ## Clean output files and cache
	rm -rf output/*.json output/*.csv output/*.hash
	rm -f state.json
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

format:  ## Format code with black
	black src/ tests/ || echo "black not installed, skipping"

lint:  ## Lint code with ruff
	ruff check src/ tests/ || echo "ruff not installed, skipping"

demo:  ## Run with mock data (no API key needed)
	python demo_with_mock_data.py
