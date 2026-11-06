# Project title

![CI](https://github.com/sjaddya/REPO_NAME/actions/workflows/ci.yml/badge.svg)

> One sentence: what this does, on what data, for whom.
> Example: *Loads Germany's 15-minute electricity data (SMARD) into a Databricks lakehouse and shows how the renewable share drives prices.*

**Live demo:** link · **2-minute video:** link

---

## The problem

Two or three sentences. Who has this problem, and why does it matter? Keep it business-level, not technical.

## Architecture

![Architecture](docs/diagrams/architecture.png)

| Layer | What happens | Tools |
|---|---|---|
| Ingestion | … | … |
| Storage / bronze | … | … |
| Transformation / silver, gold | … | … |
| Serving | … | … |
| Orchestration & CI/CD | … | … |

## Results

The numbers a hiring manager looks for. Measure them; don't estimate.

| Measure | Value |
|---|---|
| Data freshness (source → dashboard) | … |
| Rows per run / total rows | … |
| Pipeline runtime | … |
| Tests (unit / integration / data) | … |
| Monthly cost | … |

## Key decisions

The trade-offs and why you made them. Each decision is written up in [`docs/decisions/`](docs/decisions/).

- **Decision:** reason, and what you gave up.

## How to run it

Requirements: Python 3.12, [uv](https://docs.astral.sh/uv/), Docker (if used).

```bash
git clone https://github.com/sjaddya/REPO_NAME.git
cd REPO_NAME
cp .env.example .env        # then fill in real values
make setup                  # or: uv sync && uv run pre-commit install
make check                  # lint, type-check and tests: what CI runs
```

Without `make` (Windows): run the `uv run …` line from the matching target in the `Makefile`.

## Testing

- `make test`: unit tests, no network (external APIs are mocked)
- `make test-all`: also runs integration tests against real services
- Data-quality tests: describe them here once they exist

## Limitations and next steps

Be honest. Every real system has them, and naming them shows judgement.

- …

---

## Using this template (delete this section in a real project)

1. On GitHub: **Use this template → Create a new repository**, then clone it.
2. Rename the package: `uv run python scripts/rename_project.py energy_lakehouse`
3. Replace `REPO_NAME` in this README and fill in the sections as you build.
4. `make setup`, then `make check`: everything should pass before your first commit.
5. Delete `src/<package>/http_client.py` and its tests if the project doesn't call an HTTP API.
