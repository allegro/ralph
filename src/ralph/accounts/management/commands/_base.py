# -*- coding: utf-8 -*-
"""
Base command class and utilities for extra view permissions management.

Provides shared functionality like psql-style table output formatting.
"""

import re
from typing import Callable

from django.core.management.base import BaseCommand

# Pre-compiled regex for ANSI escape codes
ANSI_ESCAPE_RE = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


def strip_ansi(text: str) -> str:
    """Remove ANSI escape codes from text."""
    return ANSI_ESCAPE_RE.sub("", text)


def calculate_column_widths(headers: list[str], rows: list[list]) -> list[int]:
    """Calculate the maximum width needed for each column."""
    widths = [len(h) for h in headers]
    for row in rows:
        for i, val in enumerate(row):
            plain_val = strip_ansi(str(val))
            widths[i] = max(widths[i], len(plain_val))
    return widths


def format_separator(widths: list[int]) -> str:
    """Format the horizontal separator line."""
    return "+-" + "-+-".join("-" * w for w in widths) + "-+"


def format_header(headers: list[str], widths: list[int]) -> str:
    """Format the header row."""
    cells = (h.ljust(widths[i]) for i, h in enumerate(headers))
    return "| " + " | ".join(cells) + " |"


def format_row(
    row: list,
    widths: list[int],
    row_idx: int,
    style_map: dict[tuple[int, int], Callable],
) -> str:
    """Format a single data row with optional styling."""
    formatted = []
    for col_idx, val in enumerate(row):
        cell = str(val).ljust(widths[col_idx])
        style_fn = style_map.get((row_idx, col_idx))
        formatted.append(style_fn(cell) if style_fn else cell)
    return "| " + " | ".join(formatted) + " |"


def format_table(
    headers: list[str],
    rows: list[list],
    style_map: dict[tuple[int, int], Callable] = None,
) -> list[str]:
    """
    Format data as psql-style table lines.

    Args:
        headers: Column header names.
        rows: List of rows, each row is a list of values.
        style_map: Optional dict mapping (row_idx, col_idx) to style function.

    Returns:
        List of formatted lines ready to print.
    """
    if not rows:
        return ["(0 rows)"]

    style_map = style_map or {}
    widths = calculate_column_widths(headers, rows)
    separator = format_separator(widths)

    lines = [
        separator,
        format_header(headers, widths),
        separator,
        *[format_row(row, widths, idx, style_map) for idx, row in enumerate(rows)],
        separator,
        f"({len(rows)} rows)",
    ]
    return lines


def format_summary(active: int, orphaned: int) -> str:
    """Format permission summary counts."""
    return (
        f"\n Active permissions:   {active}\n"
        f" Orphaned permissions: {orphaned}\n"
        f" Total in database:    {active + orphaned}\n"
    )


class PermissionBaseCommand(BaseCommand):
    """Base command with table output utilities."""

    def print_table(
        self,
        headers: list[str],
        rows: list[list],
        style_map: dict[tuple[int, int], Callable] = None,
    ):
        """Print data in psql-style table format."""
        for line in format_table(headers, rows, style_map):
            self.stdout.write(line)

    def print_summary(self, active: int, orphaned: int):
        """Print permission summary counts."""
        self.stdout.write(format_summary(active, orphaned))
