# -*- coding: utf-8 -*-
from django.contrib.admin.utils import get_fields_from_path
from django.core.urlresolvers import reverse
from django.db.models.constants import LOOKUP_SEP


def get_admin_url(obj, action):
    return reverse(
        "admin:{}_{}_{}".format(
            obj._meta.app_label, obj._meta.model_name, action
        ),
        args=(obj.id,)
    )


def get_field_by_relation_path(model, field_path):
    """
    Returns field for `model` referenced by `field_path`.

    E.g. calling:
        get_field_by_relation_path(BackOfficeAsset, 'model__manufacturer__name')
    returns:
        <django.db.models.fields.CharField: name>
    """
    return get_fields_from_path(model, field_path)[-1]


def get_value_by_relation_path(obj, field_path):
    """
    Return value of object field (which may be nested using __ notation).

    >>> get_value_by_relation_path(user, 'city__country__name')
    ... Poznan
    """
    current_field, __, rest = field_path.partition(LOOKUP_SEP)
    value = getattr(obj, current_field)
    return get_value_by_relation_path(value, rest) if rest else value
