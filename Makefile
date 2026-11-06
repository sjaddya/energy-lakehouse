# One-word commands. Each target is a plain `uv run ...` line, so if `make` is
# not installed (Windows), copy the command after the tab and run it directly.

.PHONY: setup lint format typecheck test test-all check clean

setup:        ## install dependencies and the git hooks
	uv sync
	uv run pre-commit install

lint:         ## style and bug checks
	uv run ruff check .
	uv run ruff format --check .

format:       ## fix what can be fixed automatically
	uv run ruff check --fix .
	uv run ruff format .

typecheck:    ## static types
	uv run mypy

test:         ## unit tests (fast, no network)
	uv run pytest

test-all:     ## unit + integration tests (needs network / services)
	uv run pytest --run-integration

check: lint typecheck test   ## everything CI runs

clean:
	uv run python -c "import shutil; [shutil.rmtree(p, True) for p in (\".pytest_cache\", \".mypy_cache\", \".ruff_cache\", \"htmlcov\")]"
