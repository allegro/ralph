import os
import tempfile

from dj.choices import Choices
from django import forms
from django.db import models

from ralph.assets.models.base import BaseObject
from ralph.attachments.helpers import add_attachment_from_disk
from ralph.lib.mixins.fields import BaseObjectForeignKey
from ralph.lib.mixins.models import AdminAbsoluteUrlMixin
from ralph.lib.transitions.async import RescheduleAsyncTransitionActionLater
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

    def __str__(self):
        return 'Foo: {} / {}'.format(self.id, self.bar)


class Manufacturer(models.Model):
    name = models.CharField(max_length=50)
    country = models.CharField(max_length=50)


class Car(models.Model):
    name = models.CharField(max_length=50)
    year = models.PositiveSmallIntegerField()
    manufacturer = models.ForeignKey(Manufacturer)
    manufacturer._autocomplete = False
    manufacturer._filter_title = 'test'
    foos = models.ManyToManyField(Foo)

    @classmethod
    def get_autocomplete_queryset(cls):
        return cls.objects.filter(year=2015)


class Car2(models.Model):
    manufacturer = models.ForeignKey(Manufacturer)


class Bar(models.Model):
    name = models.CharField(max_length=255)
    created = models.DateTimeField(auto_now_add=True)
    date = models.DateField()
    price = models.DecimalField(max_digits=5, decimal_places=2)
    count = models.IntegerField(default=0)
    foos = models.ManyToManyField(Foo, related_name='bars', blank=True)


class Order(
    AdminAbsoluteUrlMixin,
    models.Model,
    metaclass=TransitionWorkflowBase
):
    status = TransitionField(
        default=OrderStatus.new.id,
        choices=OrderStatus(),
    )
    remarks = models.CharField(max_length=255, blank=True, default='')

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

    @classmethod
    @transition_action(
        return_attachment=False,
    )
    def generate_exception(cls, instances, request, **kwargs):
        raise Exception('exception')


@transition_action(model=Order)
def action_registered_on_model(cls, *args, **kwargs):
    for instance in kwargs['instances']:
        instance.remarks = 'done'


class AsyncOrder(
    AdminAbsoluteUrlMixin, models.Model, metaclass=TransitionWorkflowBase
):
    status = TransitionField(
        default=OrderStatus.new.id,
        choices=OrderStatus(),
    )
    name = models.CharField(max_length=100)
    counter = models.PositiveSmallIntegerField(default=1)
    username = models.CharField(max_length=100, null=True, blank=True)
    foo = models.ForeignKey(Foo, null=True, blank=True)

    @classmethod
    @transition_action(
        verbose_name='Long runnign action',
        form_fields={
            'name': {
                'field': forms.CharField(label='name'),
            }
        },
        is_async=True
    )
    def long_running_action(cls, instances, **kwargs):
        for instance in instances:
            instance.counter += 1
            instance.name = kwargs['name']
            instance.save()

    @classmethod
    @transition_action(
        verbose_name='Another long runnign action',
        form_fields={
            'foo': {
                'field': forms.CharField(label='Foo'),
                'autocomplete_field': 'foo',
            }
        },
        is_async=True,
        run_after=['long_running_action']
    )
    def long_running_action_with_precondition(cls, instances, **kwargs):
        instance = instances[0]  # only one instance in asyc action
        instance.counter += 1
        instance.save()
        if instance.counter < 5:
            raise RescheduleAsyncTransitionActionLater()
        instance.foo = kwargs['foo']
        instance.save()

    @classmethod
    @transition_action(
        verbose_name='Assign user',
        run_after=['long_running_action']
    )
    def assing_user(cls, instances, **kwargs):
        if '_request__user' in kwargs:
            for instance in instances:
                instance.username = kwargs['_request__user'].username
                instance.save()

    @classmethod
    @transition_action(
        verbose_name='Failing action',
        is_async=True,
    )
    def failing_action(cls, instances, **kwargs):
        raise ValueError()


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


class PolymorphicTestModel(AdminAbsoluteUrlMixin, BaseObject):
    hostname = models.CharField(max_length=50)
