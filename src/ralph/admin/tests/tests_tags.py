# -*- coding: utf-8 -*-
import random

from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from ralph.accounts.tests.factories import UserFactory
from ralph.attachments.models import Attachment
from ralph.back_office.models import BackOfficeAsset
from ralph.back_office.tests.factories import BackOfficeAssetFactory
from ralph.lib.transitions.models import TransitionsHistory


class RalphTagsTest(TestCase):
    def setUp(self):
        super().setUp()
        user = UserFactory()
        back_office = BackOfficeAssetFactory()
        content_type = ContentType.objects.get_for_model(BackOfficeAsset)
        content = str.encode(str(random.random()))
        attachment = Attachment.objects.create(
            file=SimpleUploadedFile("test", content),
            uploaded_by=user,
        )
        self.history = TransitionsHistory.objects.create(
            transition_name="test",
            content_type=content_type,
            source="new",
            target="used",
            object_id=back_office.pk,
            logged_user=user,
            attachment=attachment,
        )
