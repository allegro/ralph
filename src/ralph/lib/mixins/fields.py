# -*- coding: utf-8 -*-
from django.db import models


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
