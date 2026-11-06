# One-word commands. Each target is a plain `uv run ...` line, so if `make` is
# not installed (Windows), copy the command after the tab and run it directly.
# Tools are invoked as `python -m <tool>` rather than through the generated
# .exe launchers, which Windows Smart App Control blocks inside a virtualenv.

.PHONY: setup lint format typecheck test test-all check clean

setup:        ## install dependencies and the git hooks
	uv sync
	uv run python -m pre_commit install

lint:         ## style and bug checks
	uv run python -m ruff check .
	uv run python -m ruff format --check .

format:       ## fix what can be fixed automatically
	uv run python -m ruff check --fix .
	uv run python -m ruff format .

typecheck:    ## static types
	uv run python -m mypy

test:         ## unit tests (fast, no network)
	uv run python -m pytest

test-all:     ## unit + integration tests (needs network / services)
	uv run python -m pytest --run-integration

check: lint typecheck test   ## everything CI runs

clean:
	uv run python -c "import shutil; [shutil.rmtree(p, True) for p in (\".pytest_cache\", \".mypy_cache\", \".ruff_cache\", \"htmlcov\")]"
