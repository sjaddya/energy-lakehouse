"""Rename the template's package in one step.

    uv run python scripts/rename_project.py energy_lakehouse

Renames src/data_project to src/<new_name> and replaces every reference to
`data_project` / `data-project` in the code, config and tests.
"""

import re
import sys
from pathlib import Path

OLD_PKG, OLD_DIST = "data_project", "data-project"
ROOT = Path(__file__).resolve().parent.parent
TEXT_SUFFIXES = {".py", ".toml", ".md", ".yml", ".yaml", ".cfg", ".txt"}
SKIP_DIRS = {".git", ".venv", "__pycache__", ".mypy_cache", ".ruff_cache", ".pytest_cache"}


def main() -> int:
    if len(sys.argv) != 2 or not re.fullmatch(r"[a-z][a-z0-9_]*", sys.argv[1]):
        print("usage: rename_project.py new_package_name   (lowercase, digits, underscores)")
        return 2
    new_pkg = sys.argv[1]
    new_dist = new_pkg.replace("_", "-")

    src_old, src_new = ROOT / "src" / OLD_PKG, ROOT / "src" / new_pkg
    if not src_old.exists():
        print(f"{src_old} not found: already renamed?")
        return 1

    changed = 0
    for path in ROOT.rglob("*"):
        if any(part in SKIP_DIRS for part in path.parts) or not path.is_file():
            continue
        if path.suffix not in TEXT_SUFFIXES or path.name == "rename_project.py":
            continue
        text = path.read_text(encoding="utf-8")
        new_text = text.replace(OLD_PKG, new_pkg).replace(OLD_DIST, new_dist)
        if new_text != text:
            path.write_text(new_text, encoding="utf-8")
            changed += 1

    src_old.rename(src_new)
    print(f"renamed package to {new_pkg}; updated {changed} files. Now run: uv lock && make check")
    return 0


if __name__ == "__main__":
    sys.exit(main())
