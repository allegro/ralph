# -*- coding: utf-8 -*-
from django.contrib.contenttypes.models import ContentType
from django.db.models import Prefetch
from django.test import TestCase

from ralph.lib.polymorphic.models import Polymorphic
from ralph.lib.polymorphic.tests.models import (
    PolymorphicModelBaseTest,
    PolymorphicModelTest,
    PolymorphicModelTest2,
    SomeM2MModel,
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

        self.assertIn(
            'PolymorphicModelTest: {} ({})'.format(
                self.pol_1.name, self.pol_1.pk
            ),
            result
        )
        self.assertIn(
            'PolymorphicModelTest2: {} ({})'.format(
                self.pol_3.name, self.pol_3.pk
            ),
            result
        )

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

    def test_polymorphic_queryset_ordering(self):
        r = list(PolymorphicModelBaseTest.polymorphic_objects.order_by('-name'))
        self.assertEqual(r, [self.pol_3, self.pol_2, self.pol_1])

    def test_polymorphic_queryset_use_regular_iterator(self):
        with self.assertNumQueries(1):
            list(PolymorphicModelTest.polymorphic_objects.all())

    def test_m2m_with_prefetch_related_on_polymorphic_object(self):

        sm2mm_1 = SomeM2MModel.objects.create(name='abc')
        sm2mm_1.polymorphics = [self.pol_1, self.pol_2]
        sm2mm_1 = SomeM2MModel.objects.get(name='abc')
        sm2mm_2 = SomeM2MModel.objects.create(name='def')
        sm2mm_2.polymorphics = [self.pol_2, self.pol_3]
        with self.assertNumQueries(5):
            # 5 queries:
            # 1) SomeM2MModel
            # 2) Content Types (usually cached, but turned off in tests)
            # 3) PolymorphicModelBaseTest ids
            # 4) PolymorphicModelTest based on 3)
            # 5) PolymorphicModelTest2 based on 3)
            result = {
                sm.name: sm for sm in
                SomeM2MModel.objects.prefetch_related(Prefetch(
                    lookup='polymorphics',
                    queryset=PolymorphicModelBaseTest.polymorphic_objects.polymorphic_filter(  # noqa
                        some_m2m__in=SomeM2MModel.objects.all()
                    ).all(),
                )).order_by('name')
            }
            self.assertCountEqual(
                result['abc'].polymorphics.all(),
                [self.pol_1, self.pol_2]
            )
            self.assertCountEqual(
                [inst._meta.model for inst in result['abc'].polymorphics.all()],
                [PolymorphicModelTest, PolymorphicModelTest]
            )
            self.assertCountEqual(
                result['def'].polymorphics.all(),
                [self.pol_2, self.pol_3]
            )
            self.assertCountEqual(
                [inst._meta.model for inst in result['def'].polymorphics.all()],
                [PolymorphicModelTest, PolymorphicModelTest2]
            )

    def test_m2m_with_prefetch_related_on_polymorphic_object_with_subset(self):
        """
        Test if PolymorphicModelBaseTest instance is properly fetched in
        prefetch_related when base model (SomeM2MModel in this case) is
        filtered and polymorphic_filter still contains filter for all
        SomeM2MModel objects.
        """
        sm2mm_1 = SomeM2MModel.objects.create(name='abc')
        sm2mm_1.polymorphics = [self.pol_1, self.pol_2]
        sm2mm_1 = SomeM2MModel.objects.get(name='abc')
        sm2mm_2 = SomeM2MModel.objects.create(name='def')
        sm2mm_2.polymorphics = [self.pol_2, self.pol_3]
        sm2mm_3 = SomeM2MModel.objects.create(name='xyz')
        sm2mm_3.polymorphics = [self.pol_2]
        sm2mm_4 = SomeM2MModel.objects.create(name='qwerty')
        sm2mm_4.polymorphics = [self.pol_2]
        with self.assertNumQueries(4):
            result = {
                sm.name: sm for sm in
                SomeM2MModel.objects.filter(name='xyz').prefetch_related(
                    Prefetch(
                        lookup='polymorphics',
                        queryset=PolymorphicModelBaseTest.polymorphic_objects.polymorphic_filter(  # noqa
                            some_m2m__in=SomeM2MModel.objects.all()
                        ).all(),
                    )
                ).order_by('name')
            }
            self.assertCountEqual(
                result['xyz'].polymorphics.all(),
                [self.pol_2]
            )
