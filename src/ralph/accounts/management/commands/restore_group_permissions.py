"""
Management command to restore group permissions from a JSON file.
"""

import json

from django.contrib.auth.models import Group, Permission
from django.core.management.base import CommandError

from ralph.accounts.management.commands._base import PermissionBaseCommand


def assign_permission_to_group(group_name: str, perm_key: str) -> tuple[bool, str | None]:
    """
    Assign permission to group. Returns (success, error).

    perm_key format: "app_label.codename" (e.g., "accounts.can_view_extra_dnsview")
    """
    try:
        group = Group.objects.get(name=group_name)
    except Group.DoesNotExist:
        return False, f"Group '{group_name}' not found"

    try:
        app_label, codename = perm_key.split(".", 1)
        perm = Permission.objects.get(
            codename=codename,
            content_type__app_label=app_label,
        )
    except ValueError:
        return (
            False,
            f"Invalid permission format '{perm_key}' (expected 'app_label.codename')",
        )
    except Permission.DoesNotExist:
        return False, f"Permission '{perm_key}' not found"

    group.permissions.add(perm)
    return True, None


class Command(PermissionBaseCommand):
    help = "Restore group permissions from a JSON file."

    def add_arguments(self, parser):
        parser.add_argument(
            "file",
            help="Input JSON file path.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be done without making changes.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        try:
            with open(options["file"], "r") as f:
                mappings = json.load(f)
        except FileNotFoundError as e:
            raise CommandError(f"File not found: {options['file']}") from e
        except json.JSONDecodeError as e:
            raise CommandError(f"Invalid JSON file: {e}") from e

        headers = ["group", "permission", "status"]
        rows = []
        style_map = {}
        row_idx = 0

        for group_name, perm_keys in mappings.items():
            for perm_key in perm_keys:
                if dry_run:
                    rows.append([group_name, perm_key, "WOULD ASSIGN"])
                    style_map[(row_idx, 2)] = self.style.NOTICE
                else:
                    success, error = assign_permission_to_group(group_name, perm_key)
                    if success:
                        rows.append([group_name, perm_key, "ASSIGNED"])
                        style_map[(row_idx, 2)] = self.style.SUCCESS
                    else:
                        rows.append([group_name, perm_key, error])
                        style_map[(row_idx, 2)] = self.style.WARNING
                row_idx += 1

        if rows:
            self.stdout.write("\n")
            self.print_table(headers, rows, style_map)

        action = "Would restore" if dry_run else "Restored"
        self.stdout.write(self.style.SUCCESS(f"\n{action} {len(rows)} assignment(s)."))
