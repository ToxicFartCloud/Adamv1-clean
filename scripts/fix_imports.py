#!/usr/bin/env python3
"""Utility to update imports after project restructuring."""

import re
from pathlib import Path

MAPPING = {
    r"from adam_base import": "from src.adam.core import",
    r"import adam_base": "import src.adam.core as adam_base",
    r"from server\.app import": "from src.server.main import",
    r"from ui\.UI import": "from src.ui.app import",
    r"from adam_tools\.plugins": "from plugins",
}

SKIP_DIRS = {"archive", "__pycache__"}


def fix_file(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    updated = text
    for pattern, replacement in MAPPING.items():
        updated = re.sub(pattern, replacement, updated)
    if updated != text:
        path.write_text(updated, encoding="utf-8")
        print(f"Fixed: {path}")


def main() -> None:
    root = Path(".").resolve()
    for file_path in root.rglob("*.py"):
        if any(part in SKIP_DIRS for part in file_path.parts):
            continue
        if file_path.is_file():
            fix_file(file_path)


if __name__ == "__main__":
    main()
