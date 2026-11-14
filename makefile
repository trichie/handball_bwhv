.PHONY: format lint ty ruff ruff-ty clean tidy

format:
	@echo "Formatting the project..."
	ruff format .

lint:
	@echo "Linting the project..."
	ruff check . --fix --unsafe-fixes

ty:
	@echo "Type checking the project..."
	ty check .

ruff: lint format

ruff-ty: lint format ty

clean:
	@echo "Cleaning Python build artifacts..."
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -exec rm -rf {} +
	rm -rf .pytest_cache .mypy_cache .ruff_cache .coverage htmlcov
	rm -rf build/ *.egg-info

tidy: ruff-ty clean