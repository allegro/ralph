import os
import tempfile

from dj.choices import Choices
from django.db import models

from ralph.attachments.helpers import add_attachment_from_disk
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


class Order(
    AdminAbsoluteUrlMixin,
    models.Model,
    metaclass=TransitionWorkflowBase
):
    status = TransitionField(
        default=OrderStatus.new.id,
        choices=OrderStatus(),
    )

    @classmethod
    @transition_action(return_attachment=True)
    def pack(cls, instances, request, **kwargs):
        path = os.path.join(tempfile.gettempdir(), 'test.txt')
        with open(path, 'w') as f:
            f.write('test')
        return add_attachment_from_disk(
            instances, path, request.user, 'pack action'
        )

    @classmethod
    @transition_action(
        return_attachment=True,
        verbose_name='Go to post office',
    )
    def go_to_post_office(cls, instances, **kwargs):
        pass


class TestAsset(models.Model):
    hostname = models.CharField(max_length=50)
    sn = models.CharField(max_length=200, null=True, blank=True, unique=True)
    barcode = models.CharField(
        max_length=200, null=True, blank=True, unique=True, default=None,
    )
