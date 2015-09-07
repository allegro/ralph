from dj.choices import Choices
from django.db import models

from ralph.lib.mixins.models import AdminAbsoluteUrlMixin
from ralph.lib.transitions import (
    transition_action,
    TransitionField,
    TransitionWorkflowBase
)


class OrderStatus(Choices):
    _ = Choices.Choice

    new = _('new')
    to_send = _('to_send')
    sended = _('sended')


class Foo(AdminAbsoluteUrlMixin, models.Model):
    bar = models.CharField('bar', max_length=50)


class Manufacturer(models.Model):
    name = models.CharField(max_length=50)
    country = models.CharField(max_length=50)


class Car(models.Model):
    name = models.CharField(max_length=50)
    year = models.PositiveSmallIntegerField()
    manufacturer = models.ForeignKey(Manufacturer)


class Order(models.Model, metaclass=TransitionWorkflowBase):
    status = TransitionField(
        default=OrderStatus.new.id,
        choices=OrderStatus(),
    )

    @transition_action
    def pack(self, **kwargs):
        pass

    @transition_action
    def go_to_post_office(self, **kwargs):
        pass


class TestAsset(models.Model):
    hostname = models.CharField(max_length=50)
    sn = models.CharField(max_length=200, null=True, blank=True, unique=True)
    barcode = models.CharField(
        max_length=200, null=True, blank=True, unique=True, default=None,
    )
