# -*- coding: utf-8 -*-
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from ralph.assets.models.base import BaseObject
from ralph.back_office.models import BackOfficeAsset
from ralph.data_center.models import DataCenterAsset
from ralph.tests.models import BaseObjectForeignKeyModel


class BaseObjectForeignKeyTestCase(TestCase):
    def test_limit_choices(self):
        model = BaseObjectForeignKeyModel.objects.create(
            base_object=BaseObject.objects.create()
        )
        bo_field = model._meta.get_field('base_object')
        content_types = ContentType.objects.get_for_models(
            BackOfficeAsset, DataCenterAsset
        )
        content_type_result = bo_field.limit_choices()['content_type__in']
        self.assertListEqual(
            [i.id for i in content_type_result],
            [i.id for i in content_types.values()]
        )
