.PHONY: install test lint format typecheck bench demo clean

install:
	pip install -e ".[dev]"

test:
	pytest --cov=zea --cov-report=term-missing

lint:
	ruff check zea/

format:
	ruff format zea/

typecheck:
	mypy zea/

bench:
	python -m tests.benchmark.runner --quick

demo:
	zea analyze . --output .zea

clean:
	rm -rf .zea/ .coverage htmlcov/ dist/ build/ *.egg-info __pycache__
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
