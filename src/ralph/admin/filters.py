# -*- coding: utf-8 -*-
import re
from datetime import datetime
from functools import lru_cache

from django.contrib.admin import SimpleListFilter
from django.contrib.admin.filters import FieldListFilter
from django.contrib.admin.utils import get_model_from_relation
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import Q
from django.forms.utils import flatatt
from django.utils.encoding import smart_text
from django.utils.formats import get_format
from django.utils.html import conditional_escape, mark_safe
from django.utils.translation import ugettext_lazy as _
from mptt.fields import TreeForeignKey
from mptt.settings import DEFAULT_LEVEL_INDICATOR
from taggit.managers import TaggableManager

from ralph.admin.autocomplete import DETAIL_PARAM, QUERY_PARAM
from ralph.admin.helpers import get_field_by_relation_path

SEARCH_SEPARATORS_REGEX = re.compile(r'[;|]')


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
        try:
            if field.flatchoices:
                self.choices_list = field.flatchoices
        except AttributeError:
            pass
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


class NumberListFilter(DateListFilter):

    """Renders filter form with decimal field."""

    template = 'admin/filters/number_filter.html'

    def queryset(self, request, queryset):
        if any(self.value()):
            value = self.value()
            if value[0]:
                queryset = queryset.filter(**{
                    '{}__gte'.format(self.field_path): value[0]
                })
            if value[1]:
                queryset = queryset.filter(**{
                    '{}__lte'.format(self.field_path): value[1]
                })
        return queryset

    def choices(self, cl):
        value = self.value()
        # default is decimal
        step = 0.01
        if isinstance(self.field, models.IntegerField):
            step = 1

        yield {
            'parameter_name_start': self.parameter_name_start,
            'parameter_name_end': self.parameter_name_end,
            'start_value': value[0],
            'end_value': value[1],
            'step': step
        }


class TextListFilter(BaseCustomFilter):

    """Renders filter form with char field."""

    template = "admin/filters/text_filter.html"

    def queryset(self, request, queryset):
        if self.value():
            query = Q()
            for value in SEARCH_SEPARATORS_REGEX.split(self.value()):
                query |= Q(
                    **{'{}__icontains'.format(self.field_path): value.strip()}
                )
            return queryset.filter(query)

    def choices(self, cl):
        return ({
            'current_value': self.value(),
            'parameter_name': self.field_path
        },)


class TagsListFilter(TextListFilter):

    """Filter by taggit tags."""

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(tags__name__in=SEARCH_SEPARATORS_REGEX.split(
                self.value()
            ))


class RelatedFieldListFilter(ChoicesListFilter):
    """
    Filter for related fields (ForeignKeys) which is displayed as regular HTML
    select list (all options are fetched at once).
    """
    def label_for_instance(self, obj):
        return smart_text(obj)

    @property
    def choices_list(self):
        model = get_model_from_relation(self.field)
        queryset = model._default_manager.all()
        return [(i._get_pk_val(), self.label_for_instance(i)) for i in queryset]


class RelatedAutocompleteFieldListFilter(RelatedFieldListFilter):

    """Filter for Foregin key field."""

    template = "admin/filters/related_filter.html"
    empty_value = '##@_empty_@##'

    def __init__(self, field, request, params, model, model_admin, field_path):
        super().__init__(field, request, params, model, model_admin, field_path)
        self.field_model = get_model_from_relation(self.field)

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            if value == self.empty_value:
                queryset = queryset.filter(
                    **{'{}__isnull'.format(self.field_path): True}
                )
            else:
                queryset = queryset.filter(**{self.field_path: value})
        return queryset

    def get_related_url(self):
        return reverse(
            'admin:%s_%s_changelist' % (
                self.field_model._meta.app_label,
                self.field_model._meta.model_name,
            ),
        )

    def choices(self, cl):
        model_options = (
            self.field_model._meta.app_label, self.field_model._meta.model_name
        )
        model = get_field_by_relation_path(
            self.model, self.field_path
        ).model
        widget_options = {
            'data-suggest-url': reverse(
                'autocomplete-list', kwargs={
                    'app': model._meta.app_label,
                    'model': model.__name__,
                    'field': self.field.name
                }
            ),
            'data-details-url': reverse(
                'admin:{}_{}_autocomplete_details'.format(*model_options)
            ),
            'data-query-var': QUERY_PARAM,
            'data-detail-var': DETAIL_PARAM,
            'data-target-selector': '#id_{}'.format(self.field_path)
        }
        value = self.value()
        current_object = None
        if value:
            if value == self.empty_value:
                current_object = '<empty>'
            else:
                try:
                    current_object = self.field_model.objects.get(
                        pk=int(value)
                    )
                except self.field_model.DoesNotExist:
                    pass

        return ({
            'current_value': self.value(),
            'parameter_name': self.field_path,
            'searched_fields': [self.title],
            'related_url': self.get_related_url(),
            'name': self.field_path,
            'attrs': flatatt(widget_options),
            'current_object': current_object,
            'empty_value': self.empty_value,
            'is_empty': True
        },)


class TreeRelatedFieldListFilter(RelatedFieldListFilter):
    """
    Related filter for TreeForeignKeys.
    """
    def __init__(self, field, request, params, model, model_admin, field_path):
        self.level_indicator = DEFAULT_LEVEL_INDICATOR
        super().__init__(field, request, params, model, model_admin, field_path)

    def _get_level_indicator(self, obj):
        """
        Generates level indicator (---) for object based on object level in tree
        hierarchy.
        """
        level = getattr(obj, obj._mptt_meta.level_attr)
        return mark_safe(conditional_escape(self.level_indicator) * level)

    def label_for_instance(self, obj):
        level_indicator = self._get_level_indicator(obj)
        return mark_safe(
            level_indicator + ' ' + conditional_escape(smart_text(obj))
        )


class LiquidatedStatusFilter(SimpleListFilter):

    title = _('show liquidated')
    parameter_name = 'liquidated'
    template = "admin/filters/checkbox_filter.html"

    def __init__(self, request, params, model, model_admin):
        super().__init__(request, params, model, model_admin)
        self.model = model

    def lookups(self, request, model_admin):
        return (
            (1, _('show liquidated')),
        )

    def choices(self, cl):
        yield {
            'selected': self.value() or False,
            'parameter_name': self.parameter_name,
        }

    def queryset(self, request, queryset):
        if not self.value():
            liquidated_status = self.model._meta.get_field(
                'status'
            ).choices.liquidated.id
            queryset = queryset.exclude(status=liquidated_status)

        return queryset


def register_custom_filters():
    """
    Register custom filters for the Django admin.
    
    This function is called in AppConfig.ready() (ralph.admin.apps).
    """
    field_filter_mapper = [
        (lambda f: bool(f.choices), ChoicesListFilter),
        (lambda f: isinstance(f, (
            models.DecimalField, models.IntegerField
        )), NumberListFilter),
        (lambda f: isinstance(f, (
            models.BooleanField, models.NullBooleanField
        )), BooleanListFilter),
        (lambda f: isinstance(f, (models.DateField)), DateListFilter),
        (lambda f: isinstance(f, (
            models.CharField, models.TextField, models.IntegerField
        )), TextListFilter),
        (
            lambda f: isinstance(f, TreeForeignKey),
            TreeRelatedFieldListFilter
        ),
        (
            lambda f: (
                isinstance(f, models.ForeignKey) and
                not getattr(f, '_autocomplete', True)
            ),
            RelatedFieldListFilter
        ),
        (
            lambda f: isinstance(f, models.ForeignKey),
            RelatedAutocompleteFieldListFilter
        ),
        (lambda f: isinstance(f, TaggableManager), TagsListFilter),
    ]

    for func, filter_class in field_filter_mapper:
        FieldListFilter.register(
            func, filter_class, take_priority=True
        )
