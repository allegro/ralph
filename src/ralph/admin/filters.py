# -*- coding: utf-8 -*-
import re
from datetime import datetime
from functools import lru_cache

from django.contrib.admin import SimpleListFilter
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


class BaseCustomFilter(SimpleListFilter):

    def has_output(self):
        return True

    def lookups(self, request, model_admin):
        return None


class ChoicesFilter(BaseCustomFilter):

    """Renders filter form with choices field."""

    template = 'admin/filters/choices_filter.html'
    choices_list = []

    def choices(self, cl):
        yield {
            'selected': False,
            'value': '',
            'display': _('All'),
            'parameter_name': self.parameter_name
        }
        for lookup, title in self.choices_list:
            yield {
                'selected': smart_text(lookup) == self.value(),
                'value': lookup,
                'display': title,
                'parameter_name': self.parameter_name,
            }

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(**{self.parameter_name: self.value()})


class BooleanFilter(ChoicesFilter):

    """Renders filter form with boolean field."""

    choices_list = [
        ('1', _('Yes')),
        ('0', _('No')),
    ]


class DateFilter(BaseCustomFilter):

    """Renders filter form with date field."""

    template = 'admin/filters/date_filter.html'

    def __init__(self, request, params, model, model_admin):
        used_parameters = {}
        for param in self.expected_parameters():
            try:
                used_parameters[param] = params.pop(param, '')
            except KeyError:
                pass
        super().__init__(request, params, model, model_admin)
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
                    '{}__gte'.format(self.parameter_name): date_start,
                })
            except ValueError:
                pass

            try:
                date_end = datetime.strptime(
                    date[1], get_format('DATE_INPUT_FORMATS')[0]
                )
                queryset = queryset.filter(**{
                    '{}__lte'.format(self.parameter_name): date_end,
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


class TextFilter(BaseCustomFilter):

    """Renders filter form with char field."""

    template = "admin/filters/text_filter.html"

    def queryset(self, request, queryset):
        if self.value():
            query = Q()
            for value in re.split(r'[;|]', self.value()):
                query |= Q(
                    **{'{}__icontains'.format(self.parameter_name): value}
                )
            return queryset.filter(query)

    def choices(self, cl):
        return ({
            'current_value': self.value(),
            'parameter_name': self.parameter_name
        },)
