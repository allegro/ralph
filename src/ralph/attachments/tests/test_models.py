import os
from tempfile import TemporaryDirectory

from ralph.accounts.tests.factories import UserFactory
from ralph.attachments.models import Attachment, AttachmentItem
from ralph.attachments.tests import AttachmentsTestCase
from ralph.tests.models import Foo, TestManufacturer


class AttachmentTest(AttachmentsTestCase):
    def test_saved_original_name(self):
        obj = Foo.objects.create(bar="test")
        filename = "test.txt"
        item = self.create_attachment_for_object(obj, filename=filename)
        self.assertFalse(item.attachment.file == item.attachment.original_filename)
        self.assertEqual(filename, item.attachment.original_filename)

    def test_get_all_attachments_for_object(self):
        self.create_attachment_for_object(Foo.objects.create(bar="test"))
        self.create_attachment_for_object(TestManufacturer.objects.create())
        obj = Foo.objects.create(bar="test")
        self.create_attachment_for_object(obj)
        self.create_attachment_for_object(obj)

        self.assertEqual(AttachmentItem.objects.get_items_for_object(obj).count(), 2)

    def test_create_from_file_path_file_name(self):
        with TemporaryDirectory() as tmp_dir_name:
            file_path = os.path.join(tmp_dir_name, "łóźć.pdf")
            with open(file_path, "w+") as f:
                f.write("content")
            attachment = Attachment.objects.create_from_file_path(
                file_path, UserFactory()
            )
            attachment.save()
            self.assertEqual(attachment.original_filename, "lozc.pdf")
