# -*- coding: utf-8 -*-
"""
Project structure check
"""

from pathlib import Path

from .result import PreCheckResult


def check_project_structure(project_root: str) -> PreCheckResult:
    """
    Check if project structure is valid

    Args:
        project_root: Project root directory

    Returns:
        PreCheckResult
    """
    project_path = Path(project_root)

    if not project_path.exists():
        return PreCheckResult(
            "Project Structure",
            False,
            f"Project root does not exist: {project_root}",
            {"path": project_root}
        )

    if not project_path.is_dir():
        return PreCheckResult(
            "Project Structure",
            False,
            f"Project root is not a directory: {project_root}",
            {"path": project_root}
        )

    # Check for common project files
    expected_items = ['backend', 'tests', 'config']
    found_items = [item for item in expected_items if (project_path / item).exists()]

    if len(found_items) >= 2:
        return PreCheckResult(
            "Project Structure",
            True,
            f"Valid project structure ({len(found_items)}/{len(expected_items)} expected dirs found)",
            {"path": project_root, "found": found_items}
        )
    else:
        return PreCheckResult(
            "Project Structure",
            False,
            f"Invalid project structure (only {len(found_items)}/{len(expected_items)} expected dirs found)",
            {"path": project_root, "found": found_items, "expected": expected_items}
        )
