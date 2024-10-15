# -*- coding: utf-8 -*-
from urllib.parse import urlencode

from django.contrib.admin.utils import get_fields_from_path
from django.contrib.contenttypes.models import ContentType
from django.db.models.constants import LOOKUP_SEP
from django.db.models.expressions import Func
from django.urls import reverse


def get_admin_url(obj, action):
    return reverse(
        "admin:{}_{}_{}".format(obj._meta.app_label, obj._meta.model_name, action),
        args=(obj.id,),
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


def get_field_title_by_relation_path(model, field_path):
    """
    Return field verbose name

    If field path is nested (using __), returned name is one before last field
    verbose name.
    """
    fields = get_fields_from_path(model, field_path)
    if len(fields) > 1:
        field = fields[-2]
    else:
        field = fields[-1]
    return field.verbose_name


def get_value_by_relation_path(obj, field_path):
    """
    Return value of object field (which may be nested using __ notation).

    >>> get_value_by_relation_path(user, 'city__country__name')
    ... Poznan
    """
    current_field, __, rest = field_path.partition(LOOKUP_SEP)
    value = getattr(obj, current_field)
    return get_value_by_relation_path(value, rest) if rest else value


def getattr_dunder(obj, attr, default=None):
    """
    Gets attribute of object. Works recursively
    if attr contains double underscores.
    """

    first, dunder, rest = attr.partition("__")
    value = getattr(obj, first, default)
    if rest:
        return getattr_dunder(value, rest, default)
    return value


def get_content_type_for_model(obj):
    """
    Return content type for object model.

    If the model inherits from another model then returns the first model.

    Args:
        obj: Django object model
    Returns:
        Content Type for object model
    """
    parent_models = obj._meta.get_parent_list()
    if parent_models:
        obj = parent_models[-1]

    return ContentType.objects.get_for_model(obj)


def generate_html_link(base_url, label, params=None):
    """
    Generate html link.

    Args:
        base_url: Url
        params: dict of params
        label: Label in link

    Returns:
        string html

    Example:
        >>> generate_html_link(
            'http://ralph.com/', {'param': 'value'}, 'Ralph'
        )
        >>> <a href="http://ralph.com/?param=value">Ralph</a>
    """

    return '<a href="{base_url}{params}">{label}</a>'.format(
        base_url=base_url,
        params=("?" + urlencode(params or {})) if params else "",
        label=str(label).replace(" ", "&nbsp;"),
    )


def get_client_ip(request):
    """
    Return client's IP.

    Args:
        request: Django's request object

    Returns:
        IP as a string
    """
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


class CastToInteger(Func):
    """
    A helper class for casting values to signed integer in database.
    """

    function = "CAST"
    template = "%(function)s(%(expressions)s as %(integer_type)s)"

    def __init__(self, *expressions, **extra):
        super().__init__(*expressions, **extra)
        self.extra["integer_type"] = "INTEGER"

    def as_mysql(self, compiler, connection):
        self.extra["integer_type"] = "SIGNED"
        return super().as_sql(compiler, connection)
