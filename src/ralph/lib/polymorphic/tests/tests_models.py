# -*- coding: utf-8 -*-
from django.contrib.contenttypes.models import ContentType
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
        cls.sth_related = SomethingRelated.objects.create(name="Rel1")
        cls.pol_1 = PolymorphicModelTest.objects.create(
            name="Pol1", sth_related=cls.sth_related
        )
        cls.pol_2 = PolymorphicModelTest.objects.create(
            name="Pol2", sth_related=cls.sth_related
        )
        cls.pol_3 = PolymorphicModelTest2.objects.create(
            name="Pol3",
            another_related=cls.sth_related,
        )

    def test_polymorphic_metaclass(self):
        self.assertIn(Polymorphic, list(getattr(self.pol_1, "_polymorphic_models")))

    def test_content_type_save(self):
        self.assertEqual(
            self.pol_1.content_type,
            ContentType.objects.get_for_model(PolymorphicModelTest),
        )

    def test_get_descendants_models(self):
        base = PolymorphicModelBaseTest
        self.assertIn(PolymorphicModelTest, base._polymorphic_descendants)
        self.assertIn(PolymorphicModelTest2, base._polymorphic_descendants)

    def test_polymorphic_queryset(self):
        result = []
        with self.assertNumQueries(6):
            # queries:
            # select PolymorphicModelBaseTest
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
            "PolymorphicModelTest: {} ({})".format(self.pol_1.name, self.pol_1.pk),
            result,
        )
        self.assertIn(
            "PolymorphicModelTest2: {} ({})".format(self.pol_3.name, self.pol_3.pk),
            result,
        )

    def test_polymorphic_queryset_with_select_related(self):
        with self.assertNumQueries(3):
            # queries:
            # select PolymorphicModelBaseTest
            # select PolymorphicModelTest
            # select PolymorphicModelTest2
            for (
                item
            ) in PolymorphicModelBaseTest.polymorphic_objects.polymorphic_select_related(  # noqa
                PolymorphicModelTest=["sth_related"],
                PolymorphicModelTest2=["sth_related", "another_related"],
            ):
                # just get related attribute to force fetching it from DB
                item.sth_related
                if isinstance(item, PolymorphicModelTest2):
                    item.another_related

    def test_polymorphic_queryset_ordering(self):
        r = list(PolymorphicModelBaseTest.polymorphic_objects.order_by("-name"))
        self.assertEqual(r, [self.pol_3, self.pol_2, self.pol_1])

    def test_polymorphic_queryset_use_regular_iterator(self):
        with self.assertNumQueries(2):
            list(PolymorphicModelTest.polymorphic_objects.all())

    def test_m2m_with_prefetch_related_on_polymorphic_object(self):
        sm2mm_1 = SomeM2MModel.objects.create(name="abc")
        sm2mm_1.polymorphics.set([self.pol_1, self.pol_2])
        sm2mm_2 = SomeM2MModel.objects.create(name="def")
        sm2mm_2.polymorphics.set([self.pol_2, self.pol_3])
        with self.assertNumQueries(4):
            # 4 queries:
            # 1) SomeM2MModel
            # 2) PolymorphicModelBaseTest ids
            # 3) PolymorphicModelTest based on 3)
            # 4) PolymorphicModelTest2 based on 3)
            result = {
                sm.name: sm
                for sm in SomeM2MModel.objects.prefetch_related(
                    "polymorphics"
                ).order_by("name")
            }
            self.assertSetEqual(
                {obj.id for obj in result["abc"].polymorphics.all()},
                {self.pol_1.id, self.pol_2.id},
            )
            self.assertSetEqual(
                {inst._meta.model for inst in result["abc"].polymorphics.all()},
                {PolymorphicModelTest, PolymorphicModelTest},
            )
            self.assertSetEqual(
                {obj.id for obj in result["def"].polymorphics.all()},
                {self.pol_2.id, self.pol_3.id},
            )
            self.assertSetEqual(
                {inst._meta.model for inst in result["def"].polymorphics.all()},
                {PolymorphicModelTest, PolymorphicModelTest2},
            )


class PolymorphicTestCaseNew(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.sth_related = SomethingRelated.objects.create(name="Rel1")
        cls.sth_related2 = SomethingRelated.objects.create(name="Rel2")
        cls.sth_related3 = SomethingRelated.objects.create(name="Rel3")
        cls.pol_1 = PolymorphicModelTest.objects.create(
            name="Pol1", sth_related=cls.sth_related
        )
        cls.pol_2 = PolymorphicModelTest.objects.create(
            name="Pol2", sth_related=cls.sth_related2
        )
        cls.pol_3 = PolymorphicModelTest2.objects.create(
            name="Pol3",
            another_related=cls.sth_related3,
        )

    def test_polymorphics_objects_without_prefetch(self):
        """
        Iterate over objects then for each find related object resulting in N + 1 (+NUM_OF_TYPES) queries
        DON'T DO IT IN PRODUCTION CODE!
        """
        with self.assertNumQueries(6):
            (
                o1,
                o2,
                o3,
            ) = [obj for obj in PolymorphicModelBaseTest.polymorphic_objects.all()]
            self.assertEqual(o1.sth_related.name, "Rel1")
            self.assertEqual(o2.sth_related.name, "Rel2")
            self.assertEqual(o3.another_related.name, "Rel3")

    def test_polymorphics_objects_with_select_related(self):
        """
        Select related objects in both models.
        Resulting in 1 + NUM_MODELS queries (base query + separate query for each descendant model)
        """
        with self.assertNumQueries(3):
            o1, o2, o3 = [
                obj
                for obj in PolymorphicModelBaseTest.polymorphic_objects.polymorphic_select_related(
                    PolymorphicModelTest=["sth_related"],
                    PolymorphicModelTest2=["another_related"],
                ).all()
            ]
            self.assertEqual(o1.sth_related.name, "Rel1")
            self.assertEqual(o2.sth_related.name, "Rel2")
            self.assertEqual(o3.another_related.name, "Rel3")

    def test_polymorphics_objects_with_prefetch_related(self):
        """
        Prefetch related objects in both models.
        Resulting in 1 + NUM_MODELS + NUM_PREFETCHES queries
        (base query + separate query for each descendant model + separate query for each prefetch)
        """
        with self.assertNumQueries(5):
            o1, o2, o3 = [
                obj
                for obj in PolymorphicModelBaseTest.polymorphic_objects.polymorphic_prefetch_related(
                    PolymorphicModelTest=["sth_related"],
                    PolymorphicModelTest2=["another_related"],
                ).all()
            ]
            self.assertEqual(o1.sth_related.name, "Rel1")
            self.assertEqual(o2.sth_related.name, "Rel2")
            self.assertEqual(o3.another_related.name, "Rel3")

    def test_polymorphic_filter(self):
        """
        Filter objects with given field
        Resulting in 1 + NUM_MODELS (that actually have that field)
        """
        with self.assertNumQueries(2):
            (o3,) = [
                obj
                for obj in PolymorphicModelBaseTest.polymorphic_objects.polymorphic_filter(
                    another_related__name="Rel3"
                )
            ]
            self.assertEqual(o3.id, self.pol_3.id)

    def test_m2m_to_polymorphic_models(self):
        m1 = SomeM2MModel.objects.create(name="abc")
        m2 = SomeM2MModel.objects.create(name="def")
        z1 = PolymorphicModelTest.objects.create(sth_related=self.sth_related)
        z2 = PolymorphicModelTest2.objects.create(another_related=self.sth_related)
        z3 = PolymorphicModelTest.objects.create(sth_related=self.sth_related)
        z4 = PolymorphicModelTest.objects.create(sth_related=self.sth_related)
        m1.polymorphics.set([z1, z2, z3])
        m2.polymorphics.set([z2, z3, z4])

        with self.assertNumQueries(5):
            m1_, m2_ = SomeM2MModel.objects.prefetch_related(
                "polymorphics__sth_related"
            ).all()
            z1_, z2_, z3_ = [o for o in m1_.polymorphics.all()]
            self.assertListEqual([z1_.id, z2_.id, z3_.id], [z1.id, z2.id, z3.id])
            z2_, z3_, z4_ = [o for o in m2_.polymorphics.all()]
            self.assertListEqual([z2_.id, z3_.id, z4_.id], [z2.id, z3.id, z4.id])

    def test_polymorphics_objects_filter_with_prefetch(self):
        z1 = PolymorphicModelTest.objects.create(sth_related=self.sth_related)
        z2 = PolymorphicModelTest.objects.create(sth_related=self.sth_related)

        with self.assertNumQueries(4):
            (item,) = [
                item
                for item in PolymorphicModelBaseTest.polymorphic_objects.filter(
                    id=z1.id
                ).prefetch_related("sth_related")
            ]
            self.assertEqual(item.sth_related.name, "Rel1")
