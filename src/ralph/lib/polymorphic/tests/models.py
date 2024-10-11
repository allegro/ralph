# -*- coding: utf-8 -*-
from django.db import models

from ralph.lib.polymorphic.fields import PolymorphicManyToManyField
from ralph.lib.polymorphic.models import Polymorphic, PolymorphicBase


class SomethingRelated(models.Model):
    name = models.CharField(max_length=50, blank=True, null=True)


class PolymorphicModelBaseTest(Polymorphic, metaclass=PolymorphicBase):
    name = models.CharField(max_length=50, blank=True, null=True)
    sth_related = models.ForeignKey(SomethingRelated, null=True, blank=True, on_delete=models.CASCADE)

    def __str__(self):
        return "PolymorphicModelBaseTest: {} ({})".format(self.name, self.pk)


class PolymorphicModelTest(
    PolymorphicModelBaseTest,
):
    def __str__(self):
        return "PolymorphicModelTest: {} ({})".format(self.name, self.pk)


class PolymorphicModelTest2(PolymorphicModelBaseTest):
    another_related = models.ForeignKey(
        SomethingRelated, null=True, blank=True, related_name="+", on_delete=models.CASCADE
    )

    def __str__(self):
        return "PolymorphicModelTest2: {} ({})".format(self.name, self.pk)


class SomeM2MModel(models.Model):
    name = models.CharField(max_length=50)
    polymorphics = PolymorphicManyToManyField(
        PolymorphicModelBaseTest, related_name="some_m2m"
    )
