from ralph.attachments.models import AttachmentItem
from ralph.attachments.tests import AttachmentsTestCase
from ralph.tests.models import Foo, Manufacturer


class AttachmentTest(AttachmentsTestCase):
    def test_saved_original_name(self):
        obj = Foo.objects.create(bar='test')
        filename = 'test.txt'
        item = self.create_attachment_for_object(obj, filename=filename)
        self.assertFalse(
            item.attachment.file == item.attachment.original_filename
        )
        self.assertEqual(filename, item.attachment.original_filename)

    def test_get_all_attachments_for_object(self):
        self.create_attachment_for_object(Foo.objects.create(bar='test'))
        self.create_attachment_for_object(Manufacturer.objects.create())
        obj = Foo.objects.create(bar='test')
        self.create_attachment_for_object(obj)
        self.create_attachment_for_object(obj)

        self.assertEqual(
            AttachmentItem.objects.get_items_for_object(obj).count(), 2
        )
