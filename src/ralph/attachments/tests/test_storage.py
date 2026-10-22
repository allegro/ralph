import hashlib
import os
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

from botocore.exceptions import ClientError
from django.core import mail
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from ralph.accounts.tests.factories import UserFactory
from ralph.attachments.helpers import add_attachment_from_disk
from ralph.attachments.models import Attachment
from ralph.attachments.utils import send_transition_attachments_to_user
from ralph.lib.storage import DualWriteS3Storage
from ralph.tests.mixins import ClientMixin
from ralph.tests.models import Foo
from ralph.tests.s3 import FakeS3StorageMixin, client_error


class DualWriteS3StorageTest(FakeS3StorageMixin, SimpleTestCase):
    def setUp(self):
        super().setUp()
        self.storage = DualWriteS3Storage()

    def test_save_writes_both_and_read_source_can_switch_to_s3(self):
        name = self.storage.save("attachments/file.txt", ContentFile(b"content"))

        self.assertEqual(self.s3.files[("media", name)], b"content")
        with self.storage.open(name) as file_obj:
            self.assertEqual(file_obj.read(), b"content")

        self.s3.files[("media", name)] = b"S3 copy"
        with override_settings(S3_SERVE_FILES=True):
            with self.storage.open(name) as file_obj:
                self.assertEqual(file_obj.read(), b"S3 copy")
            self.assertEqual(
                self.storage.url(name),
                "https://s3.example.com/media/{}?expires=3600".format(name),
            )

    def test_save_writes_only_to_disk_when_s3_is_disabled(self):
        with override_settings(S3_STORAGE_ENABLED=False):
            name = self.storage.save("attachments/file.txt", ContentFile(b"content"))

        self.assertTrue(self.storage.local_storage.exists(name))
        self.assertEqual(self.s3.files, {})

    def test_failed_s3_upload_removes_local_file(self):
        self.s3.upload_error = client_error("500", 500, "PutObject")

        with self.assertRaises(ClientError):
            self.storage.save("attachments/file.txt", ContentFile(b"content"))

        self.assertFalse(self.storage.local_storage.exists("attachments/file.txt"))

    def test_exists_checks_s3_when_file_is_not_on_disk(self):
        self.s3.files[("media", "attachments/s3-only.txt")] = b"content"

        self.assertTrue(self.storage.exists("attachments/s3-only.txt"))
        self.assertFalse(self.storage.exists("attachments/missing.txt"))

        name = self.storage.save("attachments/s3-only.txt", ContentFile(b"new"))
        self.assertNotEqual(name, "attachments/s3-only.txt")
        self.assertEqual(self.s3.files[("media", "attachments/s3-only.txt")], b"content")

    def test_delete_removes_file_from_both_storages(self):
        name = self.storage.save("attachments/file.txt", ContentFile(b"content"))

        self.storage.delete(name)

        self.assertFalse(self.storage.local_storage.exists(name))
        self.assertNotIn(("media", name), self.s3.files)

    def test_open_falls_back_to_local_file_missing_in_s3(self):
        name = self.storage.local_storage.save("attachments/file.txt", ContentFile(b"legacy"))

        with override_settings(S3_SERVE_FILES=True):
            with self.assertLogs("ralph.lib.storage", level="WARNING"):
                with self.storage.open(name) as file_obj:
                    self.assertEqual(file_obj.read(), b"legacy")

    def test_open_raises_file_not_found_when_file_is_missing_everywhere(self):
        with override_settings(S3_SERVE_FILES=True):
            with self.assertRaises(FileNotFoundError):
                self.storage.open("attachments/missing.txt")

    def test_open_does_not_hide_other_s3_errors(self):
        name = self.storage.save("attachments/file.txt", ContentFile(b"content"))
        self.s3.download_error = client_error("403", 403, "HeadObject")

        with override_settings(S3_SERVE_FILES=True):
            with self.assertRaises(ClientError):
                self.storage.open(name)

    def test_backfill_is_idempotent(self):
        name = self.storage.local_storage.save("attachments/file.txt", ContentFile(b"legacy"))

        self.assertTrue(self.storage.copy_local_to_s3(name))
        self.assertFalse(self.storage.copy_local_to_s3(name))
        self.assertEqual(self.s3.files[("media", name)], b"legacy")


class AttachmentS3Test(FakeS3StorageMixin, ClientMixin, TestCase):
    def _create_attachment(self, content, filename="report.pdf"):
        return Attachment.objects.create(
            file=SimpleUploadedFile(filename, content),
            uploaded_by=UserFactory(),
            mime_type="application/pdf",
        )

    def test_serve_attachment_reads_from_s3(self):
        attachment = self._create_attachment(b"local content")
        self.s3.files[("media", attachment.file.name)] = b"S3 content"
        self.login_as_user()

        with override_settings(S3_SERVE_FILES=True):
            response = self.client.get(
                reverse("serve_attachment", args=(attachment.id, attachment.original_filename))
            )
            content = b"".join(response.streaming_content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(content, b"S3 content")

    def test_send_transition_attachments_reads_from_s3(self):
        attachment = self._create_attachment(b"local content")
        self.s3.files[("media", attachment.file.name)] = b"S3 content"
        attachment = Attachment.objects.get(pk=attachment.pk)
        requester = UserFactory(email="requester@example.com")

        def context_func(transition_name):
            return SimpleNamespace(subject="Subject", body="Body", from_email="ralph@example.com")

        with patch(
            "ralph.attachments.utils.Transition.objects.get",
            return_value=SimpleNamespace(name="transition"),
        ):
            with override_settings(S3_SERVE_FILES=True):
                send_transition_attachments_to_user(
                    requester, 1, context_func, attachments=[attachment]
                )

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            list(mail.outbox[0].attachments),
            [("report.pdf", b"S3 content", "application/pdf")],
        )

    def test_add_attachment_from_disk_does_not_read_back_from_s3(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = os.path.join(tmp_dir, "report.pdf")
            with open(file_path, "wb") as f:
                f.write(b"report")

            with override_settings(S3_SERVE_FILES=True):
                attachment = add_attachment_from_disk(
                    Foo.objects.create(bar="test"), file_path, UserFactory()
                )

        self.assertEqual(attachment.md5, hashlib.md5(b"report").hexdigest())
        self.assertEqual(attachment.mime_type, "application/pdf")
        self.assertEqual(self.s3.files[("media", attachment.file.name)], b"report")
        self.assertEqual(self.s3.downloads, [])
