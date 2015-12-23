# -*- coding: utf-8 -*-
from django import forms
from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.db import models


class NullableFormFieldMixin(object):
    def to_python(self, value):
        "Returns a Unicode object."
        if value in self.empty_values:
            return None
        return super().to_python(value)


class NullableCharFormField(NullableFormFieldMixin, forms.CharField):
    pass


class NullableGenericIPAddressFormField(
    NullableFormFieldMixin, forms.GenericIPAddressField
):
    pass


class NullableCharFieldMixin(object):
    """
    Mixin for char fields and descendants which will replace empty string value
    ('') by null when saving to the database.

    It's especially usefull when field is marked as unique and at the same time
    allows null/blank (`models.CharField(unique=True, null=True, blank=True)`)
    """
    _formfield_class = NullableCharFormField

    def to_python(self, value):
        return super().to_python(value) or ''

    def get_prep_value(self, value):
        return super().get_prep_value(value) or None

    def formfield(self, **kwargs):
        defaults = {}
        if self._formfield_class:
            defaults['form_class'] = self._formfield_class
        defaults.update(kwargs)
        return super().formfield(**defaults)


class NullableCharField(
    NullableCharFieldMixin,
    models.CharField,
    metaclass=models.SubfieldBase
):
    pass


class NullableGenericIPAddressField(
    NullableCharFieldMixin,
    models.GenericIPAddressField
):
    _formfield_class = NullableGenericIPAddressFormField


class BaseObjectForeignKey(models.ForeignKey):
    """
    Base object Foreign Key.

    Add support for additional parameter limit_models for
    Foreign Key field.

    """
    def __init__(self, *args, **kwargs):
        kwargs['limit_choices_to'] = self.limit_choices
        self.limit_models = kwargs.pop('limit_models', [])
        super().__init__(*args, **kwargs)

    def limit_choices(self):
        """
        Add limit_choices_to search by content_type for models
        inherit Polymorphic
        """
        if self.limit_models:
            content_types = ContentType.objects.get_for_models(
                *[apps.get_model(*i.split('.')) for i in self.limit_models]
            )
            return {'content_type__in': content_types.values()}

        return {}

    def get_limit_models(self):
        """
        Returns Model class list from limit_models.
        """
        return [apps.get_model(model) for model in self.limit_models]
