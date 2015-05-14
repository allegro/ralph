# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from six import with_metaclass

from django.db import models
from django.db.models.base import ModelBase
from django.utils.translation import ugettext_lazy as _


class PermissionByFieldBase(ModelBase):
    """Extends permissions by edit per field of model."""
    def __new__(cls, name, bases, attrs):
        new_class = super(PermissionByFieldBase, cls).__new__(
            cls, name, bases, attrs
        )
        for field in new_class._meta.fields:
            name = field.name
            new_class._meta.permissions.append((
                'can_edit_{}_field'.format(name),
                _('Can edit {} field').format(name)
            ))
        return new_class


class PermByFieldMixin(with_metaclass(PermissionByFieldBase, models.Model)):

    # TODO
    def have_access_to_field(self, field, user=None, group=None):
        pass

    # TODO
    @property
    def allowed_fields(self, user=None, group=None):
        pass

    class Meta:
        abstract = True
