#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Common models."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from collections import namedtuple

from dj.choices import Choices
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.generic import GenericForeignKey
from django.db import models as db
from django.db.utils import DatabaseError
from django.dispatch import Signal
from django import forms
from django.utils.translation import ugettext_lazy as _
from tastypie.models import create_api_key

from ralph.settings import SYNC_FIELD_MIXIN_NOTIFICATIONS_WHITELIST

ChangeTuple = namedtuple('ChangeTuple', ['field', 'old_value', 'new_value'])


def create_api_key_ignore_dberrors(*args, **kwargs):
    try:
        return create_api_key(*args, **kwargs)
    except DatabaseError:
        # no such table yet, first syncdb
        from django.db import transaction
        transaction.rollback_unless_managed()

db.signals.post_save.connect(create_api_key_ignore_dberrors, sender=User)


# signal used by SyncFieldMixin for sending notifications on changed fields
fields_synced_signal = Signal(providing_args=['changes', 'change_author'])


class SyncFieldMixin(db.Model):
    """
    Mixin responsible for syncing fields between linked objects. In order to
    specify objects and fields that you want to keep in sync, you need to
    implement 'get_synced_objs_and_fields' method which should return a list of
    tuples, where every such tuple should contain an object and a list of
    fields you want to sync, e.g.:

        [(obj1, [field1, field2]), (obj2, [field1, field3])]

    After syncing your objects, this mixin sends 'fields_synced_signal' which
    carries a list of changes that have been made.

    For example, let's say that you're changing fields 'foo' and 'bar'  on some
    device object and you want to propagate them to an asset which is linked to
    it. In order to do that, your Device class should inherit this mixin and
    implement 'get_synced_objs_and_fields' method, which should return
    something like this:

        [(linked_asset_object, ['foo', 'bar'])]

    Remember that 'linked_asset_object' should have 'foo' and 'bar' fields
    already defined - otherwise it won't make sense.
    """
    class Meta:
        abstract = True

    def get_synced_objs_and_fields(self):
        raise NotImplementedError()

    def save(self, mute=False, visited=None, *args, **kwargs):
        from ralph.ui.views.common import SAVE_PRIORITY
        # by default save with the same priority as in 'edit device' forms etc.
        visited = visited or set()
        visited.add(self)
        priority = kwargs.get('priority')
        change_author = kwargs.get('user')
        if priority is None:
            priority = SAVE_PRIORITY
        changes = []
        for obj, fields in self.get_synced_objs_and_fields():
            if obj in visited:
                continue
            for f in fields:
                setattr(obj, f, getattr(self, f))
            obj.save(visited=visited, mute=True, priority=priority)
        # if 'mute' is False *and* if the given field is not present in
        # SYNC_FIELD_MIXIN_NOTIFICATIONS_WHITELIST, *then* notification of
        # change won't be send
        if not mute:
            changes = []
            try:
                old_obj = type(self).objects.get(pk=self.pk)
            except type(self).DoesNotExist:
                old_obj = None
            for field in self._meta.fields:
                if field.name not in SYNC_FIELD_MIXIN_NOTIFICATIONS_WHITELIST:
                    continue
                old_value = getattr(old_obj, field.name) if old_obj else None
                new_value = getattr(self, field.name)
                if old_value != new_value:
                    changes.append(
                        ChangeTuple(field.name, old_value, new_value)
                    )
            fields_synced_signal.send_robust(
                sender=self, changes=changes, change_author=change_author
            )
        return super(SyncFieldMixin, self).save(*args, **kwargs)


class CustomAttributeTypes(Choices):
    _ = Choices.Choice

    INTEGER = _('Integer')
    STRING = _('String')
    SINGLE_CHOICE = _('Single Choice')


class CustomAttribute(db.Model):
    """A custom attribute that can be attached to any model."""

    name = db.CharField(max_length=255)
    verbose_name = db.CharField(
        verbose_name=_('Displayed name'),
        max_length=255,
    )
    type = db.PositiveIntegerField(
        choices=CustomAttributeTypes()
    )
    content_type = db.ForeignKey(ContentType)
    required = db.BooleanField()

    def load_attributes_if_necessary(self, inst):
        """
        Reloads the custom attribute values for instance if they are not loaded
        """
        if self.name not in inst.__dict__:
            inst.load_custom_attributes()

    def is_option_based(self):
        """Returns true if this attribute uses options"""
        return self.type in {CustomAttributeTypes.SINGLE_CHOICE}

    def __unicode__(self):
        return self.verbose_name

    def __get__(self, inst, cls):
        if self.name not in inst.__dict__:
            inst.load_custom_attributes()
        return inst.__dict__[self.name]

    def __set__(self, inst, value):
        if self.is_option_based() and isinstance(value, basestring):
            try:
                value = CustomAttributeOption.objects.get(
                    value=value,
                    custom_attribute=self,
                )
            except CustomAttributeOption.DoesNotExist:
                raise ValueError('Custom attribute {} has no option {}'.format(
                    str(self), value
                ))
        self.load_attributes_if_necessary(inst)
        inst.__dict__[self.name] = value
        value_object = inst.ca_values[self.type].get(self.pk)
        if value_object is None:
            value_object = CA_TYPE2MODEL[self.type](
                attribute=self,
                value=value,
                object_id=inst.pk,
                content_type=type(inst).content_type,
            )
            inst.ca_values[self.type][self.pk] = value_object
        else:
            value_object.value = value
        value_object.dirty = True

    def save(self, *args, **kwargs):
        super(CustomAttribute, self).save(*args, **kwargs)
        self.content_type.model_class().refresh_custom_attributes()


class CustomAttributeValue(db.Model):
    """An abstract custom attribute value."""
    attribute = db.ForeignKey(CustomAttribute)
    # The below is a redundancy, but it works well with django and also
    # allows for model inheritance
    content_type = db.ForeignKey(ContentType)
    object_id = db.PositiveIntegerField()
    object_ = GenericForeignKey('content_type', 'object_id')

    class Meta:
        abstract = True

    def __unicode__(self):
        return '{}.{} = {}'.format(
            self.object_,
            self.attribute,
            self.value,
        )


class CustomAttributeIntegerValue(CustomAttributeValue):
    """Integer value for custom attribute"""
    value = db.IntegerField()


class CustomAttributeStringValue(CustomAttributeValue):
    """String value for custom attribute"""
    value = db.CharField(max_length=255)


class CustomAttributeOption(db.Model):
    """An option for choice fields."""
    custom_attribute = db.ForeignKey(CustomAttribute)
    value = db.CharField(max_length=255)


class CustomAttributeSingleChoiceValue(CustomAttributeValue):
    """Single choice value for custom attribute"""
    value = db.ForeignKey(CustomAttributeOption)


CA_TYPE2MODEL = {
    CustomAttributeTypes.INTEGER.id: CustomAttributeIntegerValue,
    CustomAttributeTypes.STRING.id: CustomAttributeStringValue,
    CustomAttributeTypes.SINGLE_CHOICE.id: CustomAttributeSingleChoiceValue,
}


class WithCustomAttributesMeta(type(db.Model)):
    """Metaclass for models with custom attributes"""

    def __init__(cls, clsname, bases, dict_):
        super(WithCustomAttributesMeta, cls).__init__(clsname, bases, dict_)
        cls._custom_attributes = None

    @property
    def content_type(cls):
        """The content type of this class"""
        # Only for 1.4. After 1.7 migration we can change this to get_for_model
        return ContentType.objects.get(
            app_label=cls._meta.app_label, 
            model=cls.__name__.lower()
        )

    @property
    def custom_attributes(cls):
        """Lazy-loaded list of custom attributes"""
        if cls._custom_attributes is None:
            cls.refresh_custom_attributes()
        return cls._custom_attributes

    def refresh_custom_attributes(cls):
        """Reloads custom attributes for this model"""
        if cls._custom_attributes is not None:
            for ca in cls._custom_attributes:
                delattr(cls, ca.name)
        new_custom_attributes = CustomAttribute.objects.filter(
            content_type=cls.content_type
        )
        cls._custom_attributes = new_custom_attributes
        for ca in new_custom_attributes:
            setattr(cls, ca.name, ca)
        cls.attrs_loaded = True


class WithCustomAttributes(db.Model):
    """Mixin for classes with custom attributes"""

    __metaclass__ = WithCustomAttributesMeta

    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs):
        self.ca_values = None
        super(WithCustomAttributes, self).__init__(*args, **kwargs)

    def load_custom_attributes(self):
        """Loads the values for custom attributes into the __dict__ of this
        model. This method will be called once on first attempt to access the
        custom attribute."""
        self.ca_values = {}
        for type_id, Model in CA_TYPE2MODEL.items():
            values_set = Model.objects.filter(object_id=self.pk)
            self.ca_values[type_id] = {}
            for value in values_set:
                value.dirty = False
                value.to_delete = False
                self.ca_values[type_id][value.attribute.pk] = value
        for ca in type(self).custom_attributes:
            value = self.ca_values[ca.type].get(ca.pk)
            if value is not None:
                self.__dict__[ca.name] = value.value
            else:
                self.__dict__[ca.name] = None

    def save(self, *args, **kwargs):
        if self.ca_values is None:
            self.load_custom_attributes()
        ret = super(WithCustomAttributes, self).save(*args, **kwargs)
        for type_ in self.ca_values.values():
            for value_obj in type_.values():
                if value_obj.dirty:
                    value_obj.save()
                    value_obj.dirty = False
        return ret
