# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.db import models

from django_fsm import FSMIntegerField, transition

from ralph.lib.mixins.models import AdminAbsoluteUrlMixin
from ralph.lib.transitions.base import StandardWorkflowMixin


class Foo(AdminAbsoluteUrlMixin, models.Model):
    bar = models.CharField('bar', max_length=50)


class Manufacturer(models.Model):
    name = models.CharField(max_length=50)
    country = models.CharField(max_length=50)


class Car(models.Model):
    name = models.CharField(max_length=50)
    year = models.PositiveSmallIntegerField()
    manufacturer = models.ForeignKey(Manufacturer)


class Order(StandardWorkflowMixin, models.Model):
    name = models.CharField(max_length=50)
    status = FSMIntegerField(default=1)

    @transition(status, source=2, target=3)
    def send(self):
        pass
