# plugins/backup_snapshot.py

import os
import zipfile
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

try:
    import pathspec
except ImportError:
    pathspec = None

logger = logging.getLogger("adam")

METADATA = {
    "label": "Project Snapshot",
    "description": "Creates a zip archive of the project, ignoring files from .gitignore.",
    "ui_action": False,
    "executable": True,
}


def run(**kwargs) -> Dict[str, Any]:
    """
    Creates a complete zip snapshot of the project repository, respecting .gitignore.
    Optional kwargs:
        - output_dir: str (Custom directory for snapshots, defaults to ./snapshots)
    """
    if pathspec is None:
        error_msg = "'pathspec' library not installed. Please run: pip install pathspec"
        logger.error(error_msg)
        return {"ok": False, "data": None, "error": error_msg}

    try:
        # 1. Define project root and output directory
        project_root = Path(__file__).parent.parent.resolve()
        output_dir = kwargs.get("output_dir")
        snapshots_dir = Path(output_dir) if output_dir else project_root / "snapshots"
        snapshots_dir.mkdir(exist_ok=True)

        # 2. Load .gitignore patterns
        gitignore_path = project_root / ".gitignore"
        patterns = []
        if gitignore_path.is_file():
            with open(gitignore_path, "r") as f:
                patterns = f.read().splitlines()

        # Add the snapshots directory itself to the ignore list
        patterns.append(snapshots_dir.name + "/")
        spec = pathspec.PathSpec.from_lines("gitwildmatch", patterns)
        logger.info("Loaded .gitignore patterns for exclusion.")

        # 3. Create timestamped zip file
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        snapshot_filename = f"adam_snapshot_{timestamp}.zip"
        snapshot_path = snapshots_dir / snapshot_filename

        logger.info(f"Creating snapshot: {snapshot_path}")

        # 4. Walk and archive files
        file_count = 0
        with zipfile.ZipFile(snapshot_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(project_root):
                # Prune directories using POSIX paths
                rel_dirs = []
                for d in dirs:
                    rel_dir_path = (
                        Path(root, d).relative_to(project_root).as_posix() + "/"
                    )
                    if not spec.match_file(rel_dir_path):
                        rel_dirs.append(d)
                dirs[:] = rel_dirs

                for file in files:
                    file_path = Path(root, file)
                    try:
                        relative_path = file_path.relative_to(project_root).as_posix()
                        if not spec.match_file(relative_path):
                            zf.write(file_path, arcname=relative_path)
                            file_count += 1
                    except ValueError:
                        # File is outside project root (shouldn't happen with os.walk)
                        continue

        final_msg = (
            f"Snapshot created successfully at {snapshot_path} with {file_count} files."
        )
        logger.info(final_msg)
        return {"ok": True, "data": final_msg, "error": None}

    except Exception as e:
        error_msg = f"Snapshot creation failed: {e}"
        logger.error(error_msg, exc_info=True)
        return {"ok": False, "data": None, "error": error_msg}
