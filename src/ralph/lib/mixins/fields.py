# -*- coding: utf-8 -*-
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models.loading import get_model


class NullableCharFieldMixin(object):
    """
    Mixin for char fields and descendants which will replace empty string value
    ('') by null when saving to the database.

    It's especially usefull when field is marked as unique and at the same time
    allows null/blank (`models.CharField(unique=True, null=True, blank=True)`)
    """
    def to_python(self, value):
        return value or ''

    def get_prep_value(self, value):
        return value or None


class NullableCharField(
    NullableCharFieldMixin,
    models.CharField,
    metaclass=models.SubfieldBase
):
    pass


class NullableGenericIPAddressField(
    NullableCharField,
    models.GenericIPAddressField
):
    pass


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
                *[get_model(*i.split('.')) for i in self.limit_models]
            )
            return {'content_type__in': content_types.values()}

        return {}

    def get_limit_models(self):
        """
        Returns Model class list from limit_models.
        """
        return [get_model(model) for model in self.limit_models]
