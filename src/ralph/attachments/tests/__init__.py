# -*- coding: utf-8 -*-
import random

from django.apps import apps
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from ralph.attachments.models import Attachment, AttachmentItem

User = apps.get_model(*settings.AUTH_USER_MODEL.split("."))


class AttachmentsTestCase(TestCase):
    def create_attachment_for_object(
        self, obj, filename=None, user=None, content=b"some content"
    ):
        if not user:
            user, _ = User.objects.get_or_create(username="tester")
        if not filename:
            filename = "test"
        content += str.encode(str(random.random()))
        attachment = Attachment.objects.create(
            file=SimpleUploadedFile(filename, content),
            uploaded_by=user,
        )
        return AttachmentItem.objects.create(
            attachment=attachment,
            object_id=obj.pk,
            content_type=ContentType.objects.get_for_model(obj),
        )
