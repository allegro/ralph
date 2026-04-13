"""
Management command to list and audit extra view permissions.

This command provides an overview of all extra view permissions,
showing which are active, orphaned, and their group assignments.
"""

import json

from ralph.accounts.management.commands._base import PermissionBaseCommand
from ralph.lib.permissions.utils import collect_permission_info


class Command(PermissionBaseCommand):
    help = "List and audit all extra view permissions."

    def add_arguments(self, parser):
        parser.add_argument(
            "--show-groups",
            action="store_true",
            help="Show which groups have each permission.",
        )
        parser.add_argument(
            "--orphaned-only",
            action="store_true",
            help="Show only orphaned permissions.",
        )
        parser.add_argument(
            "--format",
            choices=["table", "json"],
            default="table",
            help="Output format (default: table).",
        )

    def handle(self, *args, **options):
        show_groups = options["show_groups"]
        orphaned_only = options["orphaned_only"]
        output_format = options["format"]

        data, active_count, orphaned_count = collect_permission_info(
            include_groups=show_groups,
            orphaned_only=orphaned_only,
        )

        if output_format == "json":
            self._output_json(data, active_count, orphaned_count)
        else:
            self._output_table(data, active_count, orphaned_count, show_groups)

    def _output_table(self, data, active_count, orphaned_count, show_groups):
        """Output permissions in psql-style table format."""
        self.print_summary(active_count, orphaned_count)

        if not data:
            self.stdout.write("(0 rows)\n")
            return

        # Build headers and rows
        headers = ["status", "codename", "name", "content_type"]
        if show_groups:
            headers.append("groups")

        rows = []
        style_map = {}

        for idx, info in enumerate(data):
            row = [info.status, info.codename, info.name, info.content_type]
            if show_groups:
                groups_str = ", ".join(info.groups) or "(none)"
                row.append(groups_str)
            rows.append(row)

            # Style the status column
            if info.is_orphaned:
                style_map[(idx, 0)] = self.style.ERROR
            else:
                style_map[(idx, 0)] = self.style.SUCCESS

        self.print_table(headers, rows, style_map)

    def _output_json(self, data, active_count, orphaned_count):
        """Output permissions in JSON format."""
        output = {
            "summary": {
                "active_count": active_count,
                "orphaned_count": orphaned_count,
                "total_count": active_count + orphaned_count,
            },
            "permissions": [
                {
                    "codename": info.codename,
                    "name": info.name,
                    "content_type": info.content_type,
                    "status": info.status,
                    "groups": info.groups,
                }
                for info in data
            ],
        }

        self.stdout.write(json.dumps(output, indent=2))
