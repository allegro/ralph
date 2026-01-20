# -*- coding: utf-8 -*-
"""
Management command to clean up orphaned extra view permissions.

Orphaned permissions are those that start with 'can_view_extra_' but are not
associated with any currently registered view. This can happen when views are
removed or when conditionally-loaded views (e.g., DNSView) are not available
in the current environment.
"""

import logging

from ralph.accounts.management.commands._base import PermissionBaseCommand
from ralph.lib.permissions.views import get_orphaned_extra_view_permissions
from ralph.lib.permissions.utils import get_permission_groups

logger = logging.getLogger(__name__)


class Command(PermissionBaseCommand):
    help = (
        "Clean up orphaned extra view permissions that are no longer "
        "associated with any registered view."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be deleted without actually deleting.",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Skip confirmation prompt.",
        )
        parser.add_argument(
            "--exclude",
            action="append",
            default=[],
            metavar="CODENAME",
            help="Exclude permission codename from deletion (can be repeated).",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        force = options["force"]
        exclude = set(options["exclude"])

        orphaned = get_orphaned_extra_view_permissions()

        if exclude:
            orphaned = orphaned.exclude(codename__in=exclude)

        if not orphaned.exists():
            self.stdout.write(
                self.style.SUCCESS("No orphaned extra view permissions found.")
            )
            return

        # Display orphaned permissions in table format
        count = orphaned.count()
        self.stdout.write(
            self.style.WARNING(f"\nFound {count} orphaned permission(s):\n")
        )

        headers = ["codename", "content_type", "groups"]
        rows = []
        style_map = {}

        for idx, perm in enumerate(orphaned):
            groups = get_permission_groups(perm)
            groups_str = ", ".join(groups) or "(none)"
            rows.append([perm.codename, str(perm.content_type), groups_str])

        self.print_table(headers, rows, style_map)

        if dry_run:
            self.stdout.write(
                self.style.NOTICE("\nDry run - no permissions were deleted.")
            )
            return

        if not force:
            self.stdout.write(
                self.style.WARNING(
                    "\nWARNING: Deleting will remove permissions from all groups!"
                )
            )
            confirm = input("Are you sure you want to delete? [y/N]: ")
            if confirm.lower() != "y":
                self.stdout.write(self.style.NOTICE("Aborted."))
                return

        deleted_count, _ = orphaned.delete()

        self.stdout.write(
            self.style.SUCCESS(f"Deleted {deleted_count} orphaned permission(s).")
        )
        logger.info(
            "Deleted %d orphaned permission(s) via management command.", deleted_count
        )
