import os
from io import StringIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings

from ralph.accounts.tests.factories import UserFactory
from ralph.attachments.models import Attachment
from ralph.deployment.models import PrebootFile, PrebootItemType
from ralph.tests.s3 import FakeS3StorageMixin


class MigrateFilesToS3CommandTest(FakeS3StorageMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.user = UserFactory()

    def _create_legacy_attachment(self, content):
        with override_settings(S3_STORAGE_ENABLED=False):
            return Attachment.objects.create(
                file=SimpleUploadedFile("legacy.txt", content),
                uploaded_by=self.user,
            )

    def _call(self, command="migrate_attachments_to_s3"):
        stdout, stderr = StringIO(), StringIO()
        call_command(command, stdout=stdout, stderr=stderr)
        return stdout.getvalue(), stderr.getvalue()

    def test_copies_local_files_and_skips_them_on_rerun(self):
        first = self._create_legacy_attachment(b"first")
        second = self._create_legacy_attachment(b"second")
        self.assertEqual(self.s3.files, {})

        stdout, _ = self._call()

        self.assertIn("2 copied, 0 already present, 0 missing", stdout)
        self.assertEqual(self.s3.files[("media", first.file.name)], b"first")
        self.assertEqual(self.s3.files[("media", second.file.name)], b"second")

        stdout, _ = self._call()

        self.assertIn("0 copied, 2 already present, 0 missing", stdout)

    def test_reports_missing_files_and_copies_the_rest(self):
        missing = self._create_legacy_attachment(b"missing")
        present = self._create_legacy_attachment(b"present")
        os.remove(os.path.join(self.media_root, missing.file.name))
        stdout, stderr = StringIO(), StringIO()

        with self.assertRaisesMessage(CommandError, "1 copied, 0 already present, 1 missing"):
            call_command("migrate_attachments_to_s3", stdout=stdout, stderr=stderr)

        self.assertIn(missing.file.name, stderr.getvalue())
        self.assertEqual(self.s3.files[("media", present.file.name)], b"present")
        self.assertNotIn(("media", missing.file.name), self.s3.files)

    def test_copies_preboot_files(self):
        with override_settings(S3_STORAGE_ENABLED=False):
            preboot_file = PrebootFile.objects.create(
                name="kernel",
                type=PrebootItemType.kernel.id,
                file=SimpleUploadedFile("vmlinuz", b"kernel"),
            )

        stdout, _ = self._call("migrate_preboot_files_to_s3")

        self.assertIn("1 copied, 0 already present, 0 missing", stdout)
        self.assertEqual(self.s3.files[("media", preboot_file.file.name)], b"kernel")

    def test_requires_enabled_s3_storage(self):
        with override_settings(S3_STORAGE_ENABLED=False):
            with self.assertRaisesMessage(CommandError, "S3 storage is not enabled"):
                self._call()
