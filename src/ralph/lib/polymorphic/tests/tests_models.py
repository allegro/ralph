# -*- coding: utf-8 -*-
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from ralph.lib.polymorphic.models import Polymorphic
from ralph.lib.polymorphic.tests.models import (
    PolymorphicModelBaseTest,
    PolymorphicModelTest
)


class PolymorphicTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.pol_1 = PolymorphicModelTest()
        cls.pol_1.name = 'Pol1'
        cls.pol_1.save()

    def test_polymorphic_metaclass(self):
        self.assertIn(
            Polymorphic, list(getattr(self.pol_1, '_polymorphic_models'))
        )

    def test_content_type_save(self):
        self.assertEqual(
            self.pol_1.content_type,
            ContentType.objects.get_for_model(PolymorphicModelTest)
        )

    def test_get_descendants_models(self):
        base = PolymorphicModelBaseTest()
        self.assertIn(PolymorphicModelTest, base._polymorphic_descendants)

    def test_polymorphic_queryset(self):
        result = [
            str(obj)
            for obj in PolymorphicModelBaseTest.polymorphic_objects.all()
        ]
        self.assertIn('PolymorphicModelTest: {}'.format(self.pol_1.pk), result)
