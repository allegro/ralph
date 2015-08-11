from django.db import models

from ralph.lib.mixins.models import AdminAbsoluteUrlMixin


class Foo(AdminAbsoluteUrlMixin, models.Model):
    bar = models.CharField('bar', max_length=50)


class Manufacturer(models.Model):
    name = models.CharField(max_length=50)
    country = models.CharField(max_length=50)


class Car(models.Model):
    name = models.CharField(max_length=50)
    year = models.PositiveSmallIntegerField()
    manufacturer = models.ForeignKey(Manufacturer)


class TestAsset(models.Model):
    hostname = models.CharField(max_length=50)
    sn = models.CharField(max_length=200, null=True, blank=True, unique=True)
    barcode = models.CharField(
        max_length=200, null=True, blank=True, unique=True, default=None,
    )
