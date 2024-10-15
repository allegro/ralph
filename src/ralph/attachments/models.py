import hashlib
import os
import string

from django.conf import settings
from django.contrib.contenttypes import fields
from django.contrib.contenttypes.models import ContentType
from django.core.files.base import ContentFile
from django.db import models, transaction
from unidecode import unidecode

from ralph.admin.helpers import get_content_type_for_model
from ralph.attachments.helpers import get_file_path
from ralph.lib.mixins.models import TimeStampMixin


class AttachmentManager(models.Manager):
    def get_attachments_for_object(self, obj):
        """
        Returns list of all related attachments to specific object.

        Example of use:
        >>> obj = DataCenterAsset.objects.get(id=2)
        >>> Attachment.objects.get_attachments_for_object(obj)
        [<Attachment: document.pdf (application/pdf) uploaded by root>]
        """
        content_type = get_content_type_for_model(obj)
        return self.get_queryset().filter(
            items__content_type=content_type,
            items__object_id=obj.id,
        )

    def create_from_file_path(self, file_path, uploaded_by):
        attachment = self.model()
        attachment.uploaded_by = uploaded_by
        filename = os.path.basename(file_path)
        attachment.original_filename = filename
        with open(file_path, "rb") as f:
            content = ContentFile(f.read())
            attachment.file.save(filename, content, save=True)
        return attachment


class AttachmentItemManager(models.Manager):
    def get_items_for_object(self, obj):
        """
        Method retruns query set contains all item related to concrete object.

        Example:
        >>> obj = DataCenterAsset.objects.get(id=2)
        >>> AttachmentItem.objects.get_items_for_object(obj)
        [<AttachmentItem: image/png data center asset: 2>]
        """
        content_type = get_content_type_for_model(obj)
        return (
            self.get_queryset()
            .select_related("attachment")
            .filter(
                object_id=obj.pk,
                content_type=content_type,
            )
        )

    def attach(self, pk, content_type, attachments):
        """
        Attach attachments to the object (through pk and content_type).
        """
        new_items = []
        for attachment in attachments:
            new_items.append(
                self.model(
                    content_type=content_type,
                    object_id=pk,
                    attachment=attachment,
                )
            )
        if new_items:
            self.bulk_create(new_items)

    def dettach(self, pk, content_type, attachments):
        """
        Dettach attachments from the object (through pk and content_type).
        """
        self.filter(
            attachment__in=attachments,
            content_type=content_type,
            object_id=pk,
        ).delete()

    @transaction.atomic
    def refresh(self, obj, new_objects=None, deleted_objects=None):
        """
        Refresh relation between object (e.g., asset, licence) and
        attachment. It is works fine with a formset.
        """
        content_type = get_content_type_for_model(obj)
        if new_objects:
            self.attach(obj.pk, content_type, new_objects)
        if deleted_objects:
            self.dettach(obj.pk, content_type, deleted_objects)


class Attachment(TimeStampMixin, models.Model):
    """
    Base model for attachment, it contains basic info about file:
        * original_filename - uploaded filename (before normalization),
        * file - the file stored on disk,
        * mime_type - mime type of file as a string, it used in HTTP response,
        * description - e.g., description of file's content or some comment,
        * uploaded_by - the user who added attachment.
    """

    md5 = models.CharField(max_length=32, unique=True)
    original_filename = models.CharField(
        max_length=255,
        unique=False,
    )
    file = models.FileField(upload_to=get_file_path, max_length=255)
    mime_type = models.CharField(
        max_length=100,
        unique=False,
        default="application/octet-stream",
    )
    description = models.TextField(blank=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    objects = AttachmentManager()

    def __str__(self):
        return "{} ({}) uploaded by {}".format(
            self.original_filename, self.mime_type, self.uploaded_by
        )

    @classmethod
    def get_md5_sum(cls, file):
        """
        Return md5 checksum of a file.
        """
        file.seek(0)
        md5 = hashlib.md5(file.read()).hexdigest()
        file.seek(0)
        return md5

    def save(self, *args, **kwargs):
        """
        Overrided standard save method. File name is saved in database
        as original name.
        """
        if not self.pk:
            self.original_filename = self._safe_filename(
                self.original_filename or self.file.name
            )
        self.md5 = self.get_md5_sum(self.file)
        super().save(*args, **kwargs)

    @staticmethod
    def _safe_filename(filename):
        """
        Returns filtered file name.

        Example:
        >>> Attachment._safe_filename('1-żółć.txt?')
        '1-zolc.txt'
        >>> Attachment._safe_filename('injection.txt?q=alert("Ha!")')
        'injection.txtqalert(Ha)''
        """
        allowed = "-_.() " + string.ascii_letters + string.digits
        return "".join(filter(lambda x: x in allowed, unidecode(filename)))


class AttachmentItem(models.Model):
    """
    This model is bridge between attachment and content type - with this
    model we can add one attachment and link with many content types.
    """

    attachment = models.ForeignKey(
        Attachment, related_name="items", on_delete=models.CASCADE
    )
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = fields.GenericForeignKey("content_type", "object_id")

    objects = AttachmentItemManager()

    def __str__(self):
        return "{} {}: {}".format(
            self.attachment.mime_type, self.content_type, self.object_id
        )
