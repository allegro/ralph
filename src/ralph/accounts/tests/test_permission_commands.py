import json
import tempfile
from io import StringIO

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from ralph.accounts.management.commands._base import (
    calculate_column_widths,
    format_header,
    format_row,
    format_separator,
    format_table,
    strip_ansi,
)
from ralph.accounts.management.commands.export_group_permissions import (
    export_all_group_permissions,
)
from ralph.accounts.management.commands.restore_group_permissions import (
    assign_permission_to_group,
)
from ralph.accounts.models import RalphUser


class BaseFormattersTestCase(TestCase):
    def test_strip_ansi_removes_escape_codes(self):
        text_with_ansi = "\x1b[31mred text\x1b[0m"
        result = strip_ansi(text_with_ansi)
        self.assertEqual(result, "red text")

    def test_strip_ansi_preserves_plain_text(self):
        plain_text = "plain text"
        result = strip_ansi(plain_text)
        self.assertEqual(result, plain_text)

    def test_calculate_column_widths_uses_header_length(self):
        headers = ["short", "longer_header"]
        rows = [["a", "b"]]
        widths = calculate_column_widths(headers, rows)
        self.assertEqual(widths, [5, 13])

    def test_calculate_column_widths_uses_row_length(self):
        headers = ["a", "b"]
        rows = [["very_long_value", "x"]]
        widths = calculate_column_widths(headers, rows)
        self.assertEqual(widths, [15, 1])

    def test_format_separator(self):
        widths = [5, 10]
        result = format_separator(widths)
        self.assertEqual(result, "+-------+------------+")

    def test_format_header(self):
        headers = ["col1", "col2"]
        widths = [5, 10]
        result = format_header(headers, widths)
        self.assertEqual(result, "| col1  | col2       |")

    def test_format_row_without_styling(self):
        row = ["val1", "val2"]
        widths = [5, 10]
        result = format_row(row, widths, 0, {})
        self.assertEqual(result, "| val1  | val2       |")

    def test_format_row_with_styling(self):
        row = ["val1", "val2"]
        widths = [5, 10]
        style_fn = lambda x: f"[{x}]"  # noqa
        style_map = {(0, 0): style_fn}
        result = format_row(row, widths, 0, style_map)
        self.assertIn("[val1 ]", result)

    def test_format_table_empty_rows(self):
        headers = ["col1", "col2"]
        rows = []
        result = format_table(headers, rows)
        self.assertEqual(result, ["(0 rows)"])

    def test_format_table_with_data(self):
        headers = ["col1", "col2"]
        rows = [["a", "b"], ["c", "d"]]
        result = format_table(headers, rows)
        self.assertEqual(
            len(result), 7
        )  # separator, header, separator, 2 rows, separator, count
        self.assertIn("(2 rows)", result[-1])


class ExportGroupPermissionsTestCase(TestCase):
    """Tests for export_group_permissions command."""

    def setUp(self):
        self.group1 = Group.objects.create(name="TestGroup1")
        self.group2 = Group.objects.create(name="TestGroup2")
        self.group_empty = Group.objects.create(name="EmptyGroup")

        # Get some existing permissions
        self.perm1 = Permission.objects.first()
        self.perm2 = Permission.objects.last()

        self.group1.permissions.add(self.perm1)
        self.group2.permissions.add(self.perm1, self.perm2)

    def test_export_all_group_permissions_function(self):
        result = export_all_group_permissions()

        self.assertIn("TestGroup1", result)
        self.assertIn("TestGroup2", result)
        self.assertNotIn("EmptyGroup", result)  # Empty groups not included

        # Check format is app_label.codename
        for perm_key in result["TestGroup1"]:
            self.assertIn(".", perm_key)

    def test_export_command_creates_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_path = f.name

        out = StringIO()
        call_command("export_group_permissions", temp_path, stdout=out)

        with open(temp_path, "r") as f:
            data = json.load(f)

        self.assertIn("TestGroup1", data)
        self.assertIn("Exported permissions for", out.getvalue())

    def test_export_format_is_app_label_codename(self):
        result = export_all_group_permissions()

        for group_name, perm_keys in result.items():
            for perm_key in perm_keys:
                parts = perm_key.split(".", 1)
                self.assertEqual(len(parts), 2)
                app_label, codename = parts
                # Verify permission exists
                self.assertTrue(
                    Permission.objects.filter(
                        codename=codename,
                        content_type__app_label=app_label,
                    ).exists()
                )


class RestoreGroupPermissionsTestCase(TestCase):
    """Tests for restore_group_permissions command."""

    def setUp(self):
        self.group = Group.objects.create(name="RestoreTestGroup")
        self.perm = Permission.objects.first()
        self.perm_key = f"{self.perm.content_type.app_label}.{self.perm.codename}"

    def test_assign_permission_to_group_success(self):
        success, error = assign_permission_to_group(self.group.name, self.perm_key)

        self.assertTrue(success)
        self.assertIsNone(error)
        self.assertIn(self.perm, self.group.permissions.all())

    def test_assign_permission_to_group_invalid_group(self):
        success, error = assign_permission_to_group("NonExistentGroup", self.perm_key)

        self.assertFalse(success)
        self.assertIn("not found", error)

    def test_assign_permission_to_group_invalid_permission(self):
        success, error = assign_permission_to_group(
            self.group.name, "invalid.permission"
        )

        self.assertFalse(success)
        self.assertIn("not found", error)

    def test_assign_permission_to_group_invalid_format(self):
        success, error = assign_permission_to_group(self.group.name, "no_dot_here")

        self.assertFalse(success)
        self.assertIn("Invalid permission format", error)

    def test_restore_command_dry_run(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({self.group.name: [self.perm_key]}, f)
            temp_path = f.name

        out = StringIO()
        call_command("restore_group_permissions", temp_path, "--dry-run", stdout=out)

        output = out.getvalue()
        self.assertIn("WOULD ASSIGN", output)
        self.assertNotIn(self.perm, self.group.permissions.all())

    def test_restore_command_actual_restore(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({self.group.name: [self.perm_key]}, f)
            temp_path = f.name

        out = StringIO()
        call_command("restore_group_permissions", temp_path, stdout=out)

        output = out.getvalue()
        self.assertIn("ASSIGNED", output)
        self.assertIn(self.perm, self.group.permissions.all())

    def test_restore_command_file_not_found(self):
        out = StringIO()
        with self.assertRaises(CommandError) as ctx:
            call_command(
                "restore_group_permissions", "/nonexistent/file.json", stderr=out
            )

        self.assertIn("File not found", str(ctx.exception))

    def test_restore_command_invalid_json(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("not valid json {{{")
            temp_path = f.name

        with self.assertRaises(CommandError) as ctx:
            call_command("restore_group_permissions", temp_path)

        self.assertIn("Invalid JSON", str(ctx.exception))


class CleanupExtraViewPermissionsTestCase(TestCase):
    """Tests for cleanup_extra_view_permissions command."""

    def setUp(self):
        # Create an orphaned extra view permission
        content_type = ContentType.objects.get_for_model(RalphUser)
        self.orphaned_perm = Permission.objects.create(
            codename="can_view_extra_orphanedtestview",
            name="Can view OrphanedTestView",
            content_type=content_type,
        )

        self.group = Group.objects.create(name="CleanupTestGroup")
        self.group.permissions.add(self.orphaned_perm)

    def test_cleanup_dry_run_does_not_delete(self):
        out = StringIO()
        call_command("cleanup_extra_view_permissions", "--dry-run", stdout=out)

        output = out.getvalue()
        self.assertIn("Dry run", output)
        self.assertTrue(
            Permission.objects.filter(
                codename="can_view_extra_orphanedtestview"
            ).exists()
        )

    def test_cleanup_with_force_deletes(self):
        out = StringIO()
        call_command("cleanup_extra_view_permissions", "--force", stdout=out)

        output = out.getvalue()
        self.assertIn("Deleted", output)
        self.assertFalse(
            Permission.objects.filter(
                codename="can_view_extra_orphanedtestview"
            ).exists()
        )

    def test_cleanup_exclude_option(self):
        out = StringIO()
        call_command(
            "cleanup_extra_view_permissions",
            "--force",
            "--exclude=can_view_extra_orphanedtestview",
            stdout=out,
        )

        # Permission should still exist because it was excluded
        self.assertTrue(
            Permission.objects.filter(
                codename="can_view_extra_orphanedtestview"
            ).exists()
        )

    def test_cleanup_no_orphaned_permissions(self):
        # Delete the orphaned permission first
        self.orphaned_perm.delete()

        out = StringIO()
        call_command("cleanup_extra_view_permissions", stdout=out)

        output = out.getvalue()
        self.assertIn("No orphaned", output)


class AuditExtraViewPermissionsTestCase(TestCase):
    """Tests for audit_extra_view_permissions command."""

    def setUp(self):
        content_type = ContentType.objects.get_for_model(RalphUser)
        self.orphaned_perm = Permission.objects.create(
            codename="can_view_extra_audittestview",
            name="Can view AuditTestView",
            content_type=content_type,
        )

    def test_audit_table_format(self):
        out = StringIO()
        call_command("audit_extra_view_permissions", stdout=out)

        output = out.getvalue()
        self.assertIn("Active permissions", output)
        self.assertIn("Orphaned permissions", output)

    def test_audit_json_format(self):
        out = StringIO()
        call_command("audit_extra_view_permissions", "--format=json", stdout=out)

        output = out.getvalue()
        data = json.loads(output)

        self.assertIn("summary", data)
        self.assertIn("permissions", data)
        self.assertIn("active_count", data["summary"])
        self.assertIn("orphaned_count", data["summary"])

    def test_audit_orphaned_only(self):
        out = StringIO()
        call_command(
            "audit_extra_view_permissions",
            "--orphaned-only",
            "--format=json",
            stdout=out,
        )

        output = out.getvalue()
        data = json.loads(output)

        for perm in data["permissions"]:
            self.assertEqual(perm["status"], "ORPHANED")

    def test_audit_show_groups(self):
        group = Group.objects.create(name="AuditTestGroup")
        group.permissions.add(self.orphaned_perm)

        out = StringIO()
        call_command(
            "audit_extra_view_permissions",
            "--show-groups",
            "--format=json",
            stdout=out,
        )

        output = out.getvalue()
        data = json.loads(output)

        # Find our test permission and check groups
        for perm in data["permissions"]:
            if perm["codename"] == "can_view_extra_audittestview":
                self.assertIn("AuditTestGroup", perm["groups"])
                break


class ExportRestoreRoundTripTestCase(TestCase):
    """Test that export and restore work together correctly."""

    def setUp(self):
        self.group = Group.objects.create(name="RoundTripTestGroup")
        self.perm = Permission.objects.first()
        self.group.permissions.add(self.perm)

    def test_export_restore_roundtrip(self):
        # Export
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_path = f.name

        call_command("export_group_permissions", temp_path)

        # Clear permissions
        self.group.permissions.clear()
        self.assertNotIn(self.perm, self.group.permissions.all())

        # Restore
        call_command("restore_group_permissions", temp_path)

        # Verify
        self.group.refresh_from_db()
        self.assertIn(self.perm, self.group.permissions.all())
