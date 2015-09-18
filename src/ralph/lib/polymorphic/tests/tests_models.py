# -*- coding: utf-8 -*-
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from ralph.lib.polymorphic.models import Polymorphic
from ralph.lib.polymorphic.tests.models import (
    PolymorphicModelBaseTest,
    PolymorphicModelTest,
    PolymorphicModelTest2,
    SomethingRelated
)


class PolymorphicTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.sth_related = SomethingRelated.objects.create(name='Rel1')
        cls.pol_1 = PolymorphicModelTest.objects.create(
            name='Pol1',
            sth_related=cls.sth_related
        )
        cls.pol_2 = PolymorphicModelTest.objects.create(
            name='Pol2',
            sth_related=cls.sth_related
        )
        cls.pol_3 = PolymorphicModelTest2.objects.create(
            name='Pol3',
            another_related=cls.sth_related,
        )

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
        base = PolymorphicModelBaseTest
        self.assertIn(PolymorphicModelTest, base._polymorphic_descendants)
        self.assertIn(PolymorphicModelTest2, base._polymorphic_descendants)

    def test_polymorphic_queryset(self):
        result = []
        with self.assertNumQueries(7):
            # queries:
            # select PolymorphicModelBaseTest
            # select content types
            # select PolymorphicModelTest
            # select SomethingRelated (from sth_related) x2
            # select PolymorphicModelTest2
            # select SomethingRelated (from another_related)
            for item in PolymorphicModelBaseTest.polymorphic_objects.all():
                result.append(str(item))
                # just get related attribute to force fetching it from DB
                item.sth_related
                if isinstance(item, PolymorphicModelTest2):
                    item.another_related

        self.assertIn('PolymorphicModelTest: {}'.format(self.pol_1.pk), result)
        self.assertIn('PolymorphicModelTest2: {}'.format(self.pol_3.pk), result)

    def test_polymorphic_queryset_with_select_related(self):
        with self.assertNumQueries(4):
            # queries:
            # select PolymorphicModelBaseTest
            # select content types
            # select PolymorphicModelTest
            # select PolymorphicModelTest2
            for item in PolymorphicModelBaseTest.polymorphic_objects.polymorphic_select_related(  # noqa
                PolymorphicModelTest=['sth_related'],
                PolymorphicModelTest2=['sth_related', 'another_related'],
            ):
                # just get related attribute to force fetching it from DB
                item.sth_related
                if isinstance(item, PolymorphicModelTest2):
                    item.another_related
