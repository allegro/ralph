# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

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
