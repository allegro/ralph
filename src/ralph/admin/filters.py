# -*- coding: utf-8 -*-
import re
from datetime import datetime
from functools import lru_cache

from django.contrib.admin.filters import FieldListFilter
from django.contrib.admin.utils import get_model_from_relation
from django.db import models
from django.db.models import Q
from django.utils.encoding import smart_text
from django.utils.formats import get_format
from django.utils.translation import ugettext_lazy as _


@lru_cache()
def date_format_to_human(value):
    """
    Convert Python format date to human.

    Example:
        >>> date_format_to_human('%Y-%m-%d')
        YYYY-MM-DD

    :param value: Date format example: %Y-%m
    """
    maps = {
        '%y': 'YY',
        '%Y': 'YYYY',
        '%m': 'MM',
        '%d': 'DD',
    }
    for k, v in maps.items():
        value = value.replace(k, v)
    return value


class BaseCustomFilter(FieldListFilter):

    """Base class for custom filters."""

    def __init__(self, field, request, params, model, model_admin, field_path):
        self.lookup_kwarg = field_path
        self.model = model
        if field.flatchoices:
            self.choices_list = field.flatchoices
        super().__init__(
            field, request, params, model, model_admin, field_path
        )

        if '__' in field_path:
            self.title = '{} {}'.format(
                field.model._meta.verbose_name,
                self.title
            )

    def value(self):
        """
        Returns the value (in string format) provided in the request's
        query string for this filter, if any. If the value wasn't provided then
        returns None.
        """
        return self.used_parameters.get(self.field_path, None)

    def has_output(self):
        return True

    def lookups(self, request, model_admin):
        return None

    def expected_parameters(self):
        return [self.lookup_kwarg]


class ChoicesListFilter(BaseCustomFilter):

    """Renders filter form with choices field."""

    template = 'admin/filters/choices_filter.html'
    _choices_list = []

    @property
    def choices_list(self):
        return self._choices_list

    @choices_list.setter
    def choices_list(self, value):
        self._choices_list = value

    def choices(self, cl):
        yield {
            'selected': False,
            'value': '',
            'display': _('All'),
            'parameter_name': self.field_path
        }

        for lookup, title in self.choices_list:
            yield {
                'selected': smart_text(lookup) == self.value(),
                'value': lookup,
                'display': title,
                'parameter_name': self.field_path,
            }

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(**{self.field_path: self.value()})


class BooleanListFilter(ChoicesListFilter):

    _choices_list = [
        ('1', _('Yes')),
        ('0', _('No')),
    ]


class DateListFilter(BaseCustomFilter):

    """Renders filter form with date field."""

    template = 'admin/filters/date_filter.html'

    def __init__(self, field, request, params, model, model_admin, field_path):
        used_parameters = {}
        self.parameter_name_start = field_path + '__start'
        self.parameter_name_end = field_path + '__end'

        for param in self.expected_parameters():
            try:
                used_parameters[param] = params.pop(param, '')
            except KeyError:
                pass
        super().__init__(
            field, request, params, model, model_admin, field_path
        )
        self.used_parameters = used_parameters

    def expected_parameters(self):
        return [self.parameter_name_start, self.parameter_name_end]

    def value(self):
        return [
            self.used_parameters.get(param)
            for param in self.expected_parameters()
        ]

    def queryset(self, request, queryset):
        if any(self.value()):
            date = self.value()
            try:
                date_start = datetime.strptime(
                    date[0], get_format('DATE_INPUT_FORMATS')[0]
                )
                queryset = queryset.filter(**{
                    '{}__gte'.format(self.field_path): date_start,
                })
            except ValueError:
                pass

            try:
                date_end = datetime.strptime(
                    date[1], get_format('DATE_INPUT_FORMATS')[0]
                )
                queryset = queryset.filter(**{
                    '{}__lte'.format(self.field_path): date_end,
                })
            except ValueError:
                pass

            return queryset

    def choices(self, cl):
        value = self.value()
        yield {
            'parameter_name_start': self.parameter_name_start,
            'parameter_name_end': self.parameter_name_end,
            'date_start': value[0],
            'date_end': value[1],
            'date_format': date_format_to_human(
                get_format('DATE_INPUT_FORMATS')[0]
            )
        }


class TextListFilter(BaseCustomFilter):

    """Renders filter form with char field."""

    template = "admin/filters/text_filter.html"

    def queryset(self, request, queryset):
        if self.value():
            query = Q()
            for value in re.split(r'[;|]', self.value()):
                query |= Q(
                    **{'{}__icontains'.format(self.field_path): value}
                )
            return queryset.filter(query)

    def choices(self, cl):
        return ({
            'current_value': self.value(),
            'parameter_name': self.field_path
        },)


class RelatedFieldListFilter(ChoicesListFilter):

    """Filter for Foregin key field."""

    @property
    def choices_list(self):
        model = get_model_from_relation(self.field)
        return [(i.id, str(i)) for i in model._default_manager.all()]


def register_custom_filters():
    """
    Register custom filters for the Django admin.
    
    This function is called in AppConfig.ready() (ralph.admin.apps).
    """
    field_filter_mapper = [
        (lambda f: bool(f.choices), ChoicesListFilter),
        (lambda f: isinstance(f, (
            models.BooleanField, models.NullBooleanField
        )), BooleanListFilter),
        (lambda f: isinstance(f, (models.DateField)), DateListFilter),
        (lambda f: isinstance(f, (
            models.CharField, models.TextField, models.IntegerField
        )), TextListFilter),
        (lambda f: isinstance(f, models.ForeignKey), RelatedFieldListFilter),
    ]

    for func, filter_class in field_filter_mapper:
        FieldListFilter.register(
            func, filter_class, take_priority=True
        )
