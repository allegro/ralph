import os
import string
from uuid import uuid4

from django.conf import settings
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.db import models, transaction
from unidecode import unidecode

from ralph.lib.mixins.models import TimeStampMixin


def get_file_path(instance, filename):
    """
    Function returns normalized filename with directory structure.
    Used in FileField as upload_to argument.

    Example:
    >>> get_file_path(object(), 'secret_shipping_document.pdf')
    'attachments/a/3/a3349176-ecac-47ff-beba-5e8480eac070.pdf'
    """
    ext = os.path.splitext(filename)[1]
    name = ''.join([str(uuid4()), ext])
    return os.path.join('attachments', name[:1], name[1:2], name)


class AttachmentManager(models.Manager):
    def get_attachments_for_object(self, obj):
        """
        Returns list of all related attachments to specific object.

        Example of use:
        >>> obj = DataCenterAsset.objects.get(id=2)
        >>> Attachment.objects.get_attachments_for_object(obj)
        [<Attachment: document.pdf (application/pdf) uploaded by root>]
        """
        content_type = ContentType.objects.get_for_model(obj)
        return self.get_queryset().filter(
            items__content_type=content_type,
            items__object_id=obj.id,
        )


class AttachmentItemManager(models.Manager):
    def get_items_for_object(self, obj):
        """
        Method retruns query set contains all item related to concrete object.

        Example:
        >>> obj = DataCenterAsset.objects.get(id=2)
        >>> AttachmentItem.objects.get_items_for_object(obj)
        [<AttachmentItem: image/png data center asset: 2>]
        """
        content_type = ContentType.objects.get_for_model(obj)
        return self.get_queryset().select_related('attachment').filter(
            object_id=obj.pk,
            content_type=content_type,
        )

    def attach(self, pk, content_type, attachments):
        """
        Attach attachemnts to the object (through pk and content_type).
        """
        new_items = []
        for attachment in attachments:
            new_items.append(self.model(
                content_type=content_type,
                object_id=pk,
                attachment=attachment,
            ))
        if new_items:
            self.bulk_create(new_items)

    def dettach(self, pk, content_type, attachments):
        """
        Dettach attachemnts from the object (through pk and content_type).
        """
        self.filter(attachment__in=attachments).delete()

    @transaction.atomic
    def refresh(self, obj, new_objects=None, deleted_objects=None):
        """
        Refresh relation between object (e.g., asset, licence) and
        attachment. It is works fine with a formset.
        """
        content_type = ContentType.objects.get_for_model(obj)
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
    original_filename = models.CharField(
        max_length=255,
        unique=False,
    )
    file = models.FileField(upload_to=get_file_path, max_length=255)
    mime_type = models.CharField(
        max_length=100,
        unique=False,
        default='application/octet-stream',
    )
    description = models.TextField(blank=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL)

    objects = AttachmentManager()

    def __str__(self):
        return '{} ({}) uploaded by {}'.format(
            self.original_filename, self.mime_type, self.uploaded_by
        )

    def save(self, *args, **kwargs):
        """
        Overrided standard save method. If object is saved first time then
        its file name is saved in database as original name.
        """
        if not self.pk:
            self.original_filename = self._safe_filename(self.file.name)
        super(Attachment, self).save(*args, **kwargs)

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
        allowed = '-_.() ' + string.ascii_letters + string.digits
        return ''.join(filter(lambda x: x in allowed, unidecode(filename)))


class AttachmentItem(models.Model):
    """
    This model is bridge between attachment and content type - with this
    model we can add one attachemnt and link with many content types.
    """
    attachment = models.ForeignKey(Attachment, related_name='items')
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    objects = AttachmentItemManager()

    def __str__(self):
        return '{} {}: {}'.format(
            self.attachment.mime_type, self.content_type, self.object_id
        )
