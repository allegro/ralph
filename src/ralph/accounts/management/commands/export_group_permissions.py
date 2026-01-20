# -*- coding: utf-8 -*-
"""
Management command to export group permissions to a JSON file.
"""

import json

from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand


def export_all_group_permissions() -> dict[str, list[str]]:
    """Export all group permissions as {group_name: ["app_label.codename", ...]}."""
    result = {}
    for group in Group.objects.prefetch_related("permissions__content_type").all():
        if group.permissions.exists():
            result[group.name] = [
                f"{perm.content_type.app_label}.{perm.codename}"
                for perm in group.permissions.all()
            ]
    return result


class Command(BaseCommand):
    help = "Export group permissions to a JSON file."

    def add_arguments(self, parser):
        parser.add_argument(
            "file",
            help="Output JSON file path.",
        )

    def handle(self, *args, **options):
        mappings = export_all_group_permissions()

        with open(options["file"], "w") as f:
            json.dump(mappings, f, indent=2)

        self.stdout.write(
            self.style.SUCCESS(
                f"Exported permissions for {len(mappings)} groups to {options['file']}"
            )
        )
