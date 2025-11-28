# -*- coding: utf-8 -*-
"""
Compiler output parser for extracting error and warning messages
"""

import re
from typing import Dict, Any, List


def parse_compile_errors(output: str) -> List[Dict[str, Any]]:
    """
    Parse compiler error messages

    Args:
        output: Compiler output (stdout + stderr)

    Returns:
        List of error dicts with file, line, column, message
    """
    errors = []

    # Patterns for different compilers
    patterns = [
        # GCC/Clang: file.cpp:line:column: error: message
        r'([^:]+):(\d+):(\d+):\s*(error|warning):\s*(.+)',
        # MSVC: file.cpp(line): error C1234: message
        r'([^(]+)\((\d+)\):\s*(error|warning)\s+\w+:\s*(.+)',
    ]

    for line in output.split('\n'):
        for pattern in patterns:
            match = re.match(pattern, line)
            if match:
                if len(match.groups()) == 5:  # GCC/Clang format
                    errors.append({
                        'file': match.group(1),
                        'line': int(match.group(2)),
                        'column': int(match.group(3)),
                        'type': match.group(4),
                        'message': match.group(5).strip(),
                    })
                elif len(match.groups()) == 4:  # MSVC format
                    errors.append({
                        'file': match.group(1),
                        'line': int(match.group(2)),
                        'column': 0,
                        'type': match.group(3),
                        'message': match.group(4).strip(),
                    })
                break

    return errors


def format_error_summary(errors: List[Dict[str, Any]]) -> str:
    """
    Format errors into a human-readable summary

    Args:
        errors: List of error dicts

    Returns:
        Formatted string summary
    """
    if not errors:
        return "No errors found"

    error_count = sum(1 for e in errors if e['type'] == 'error')
    warning_count = sum(1 for e in errors if e['type'] == 'warning')

    lines = [f"Found {error_count} error(s), {warning_count} warning(s):", ""]

    for error in errors:
        location = f"{error['file']}:{error['line']}"
        if error['column']:
            location += f":{error['column']}"
        lines.append(f"  [{error['type'].upper()}] {location}")
        lines.append(f"    {error['message']}")
        lines.append("")

    return "\n".join(lines)
