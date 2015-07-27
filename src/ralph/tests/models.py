# -*- coding: utf-8 -*-
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

    @transition(status, source=1, target=2)
    def send(self):
        pass

    @transition(status, source=1, target=2)
    def receiv(self):
        pass
