# -*- coding: utf-8 -*-
from django.db import models

from ralph.lib.polymorphic.models import (
    Polymorphic,
    PolymorphicBase,
    PolymorphicQuerySet
)


class PolymorphicModelBaseTest(
    Polymorphic,
    models.Model,
    metaclass=PolymorphicBase
):
    name = models.CharField(max_length=50, blank=True, null=True)

    polymorphic_objects = PolymorphicQuerySet.as_manager()
    objects = models.Manager()


class PolymorphicModelTest(
    PolymorphicModelBaseTest,
    models.Model,
):
    def __str__(self):
        return 'PolymorphicModelTest: {}'.format(self.pk)
