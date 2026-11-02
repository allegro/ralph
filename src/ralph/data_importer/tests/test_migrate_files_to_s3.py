import os
from io import StringIO
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings

from ralph.accounts.tests.factories import UserFactory
from ralph.attachments.models import Attachment
from ralph.deployment.models import PrebootFile, PrebootItemType
from ralph.lib.polymorphic.models import PolymorphicQuerySet
from ralph.tests.s3 import FakeS3StorageMixin
from ralph.trade_marks.tests.factories import TradeMarkFactory


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

    def test_does_not_load_all_polymorphic_rows_into_memory(self):
        with override_settings(S3_STORAGE_ENABLED=False):
            for i in range(3):
                PrebootFile.objects.create(
                    name="kernel-{}".format(i),
                    type=PrebootItemType.kernel.id,
                    file=SimpleUploadedFile("vmlinuz-{}".format(i), b"kernel"),
                )
                TradeMarkFactory(image=SimpleUploadedFile("logo-{}.png".format(i), b"logo"))

        loaded_rows = []
        original_fetch_all = PolymorphicQuerySet._fetch_all

        def fetch_all(queryset):
            original_fetch_all(queryset)
            loaded_rows.append((queryset.model.__name__, len(queryset._result_cache)))

        for command in ("migrate_preboot_files_to_s3", "migrate_trade_marks_to_s3"):
            with self.subTest(command=command):
                loaded_rows.clear()
                with patch.object(PolymorphicQuerySet, "_fetch_all", fetch_all):
                    self._call(command)

                self.assertEqual(loaded_rows, [])

    def test_requires_enabled_s3_storage(self):
        with override_settings(S3_STORAGE_ENABLED=False):
            with self.assertRaisesMessage(CommandError, "S3 storage is not enabled"):
                self._call()
