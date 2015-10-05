# -*- coding: utf-8 -*-
from django.db import models

from ralph.lib.polymorphic.models import (
    Polymorphic,
    PolymorphicBase,
    PolymorphicQuerySet
)


class SomethingRelated(models.Model):
    name = models.CharField(max_length=50, blank=True, null=True)


class PolymorphicModelBaseTest(
    Polymorphic,
    models.Model,
    metaclass=PolymorphicBase
):
    name = models.CharField(max_length=50, blank=True, null=True)
    sth_related = models.ForeignKey(SomethingRelated, null=True, blank=True)

    polymorphic_objects = PolymorphicQuerySet.as_manager()
    objects = models.Manager()


class PolymorphicModelTest(
    PolymorphicModelBaseTest,
    models.Model,
):
    def __str__(self):
        return 'PolymorphicModelTest: {}'.format(self.pk)


class PolymorphicModelTest2(PolymorphicModelBaseTest, models.Model):
    another_related = models.ForeignKey(
        SomethingRelated, null=True, blank=True, related_name='+'
    )

    def __str__(self):
        return 'PolymorphicModelTest2: {}'.format(self.pk)
