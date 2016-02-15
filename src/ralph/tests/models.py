import os
import tempfile

from dj.choices import Choices
from django.db import models

from ralph.assets.models.base import BaseObject
from ralph.attachments.helpers import add_attachment_from_disk
from ralph.lib.mixins.fields import BaseObjectForeignKey
from ralph.lib.mixins.models import AdminAbsoluteUrlMixin
from ralph.lib.transitions.decorators import transition_action
from ralph.lib.transitions.fields import TransitionField
from ralph.lib.transitions.models import TransitionWorkflowBase


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
    manufacturer._autocomplete = False
    manufacturer._filter_title = 'test'


class Car2(models.Model):
    manufacturer = models.ForeignKey(Manufacturer)


class Bar(models.Model):
    name = models.CharField(max_length=255)
    created = models.DateTimeField()
    date = models.DateField()
    price = models.DecimalField(max_digits=5, decimal_places=2)
    count = models.IntegerField(default=0)


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
        run_after=['pack'],
    )
    def go_to_post_office(cls, instances, **kwargs):
        pass


class TestAsset(models.Model):
    hostname = models.CharField(max_length=50)
    sn = models.CharField(max_length=200, null=True, blank=True, unique=True)
    barcode = models.CharField(
        max_length=200, null=True, blank=True, unique=True, default=None,
    )


class BaseObjectForeignKeyModel(models.Model):
    base_object = BaseObjectForeignKey(
        BaseObject,
        limit_models=[
            'back_office.BackOfficeAsset',
            'data_center.DataCenterAsset'
        ]
    )
