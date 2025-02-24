# -*- coding: utf-8 -*-
import ipaddress
import json
import re
from datetime import datetime
from functools import lru_cache

from django.contrib import messages
from django.contrib.admin import SimpleListFilter
from django.contrib.admin.filters import FieldListFilter
from django.contrib.admin.options import IncorrectLookupParameters
from django.contrib.admin.utils import get_model_from_relation
from django.db import models
from django.db.models import Q
from django.forms.utils import flatatt
from django.urls import reverse
from django.utils.encoding import smart_text
from django.utils.formats import get_format
from django.utils.html import conditional_escape, mark_safe
from django.utils.translation import ugettext_lazy as _
from mptt.fields import TreeForeignKey
from mptt.settings import DEFAULT_LEVEL_INDICATOR
from taggit.managers import TaggableManager

from ralph.admin.autocomplete import AUTOCOMPLETE_EMPTY_VALUE, get_results
from ralph.admin.helpers import get_field_by_relation_path
from ralph.lib.mixins.fields import MACAddressField

SEARCH_OR_SEPARATORS_REGEX = re.compile(r"[;|]")
SEARCH_AND_SEPARATORS_REGEX = re.compile(r"[&]")


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
        "%y": "YY",
        "%Y": "YYYY",
        "%m": "MM",
        "%d": "DD",
    }
    for k, v in maps.items():
        value = value.replace(k, v)
    return value


def _add_incorrect_value_message(request, label):
    messages.warning(
        request, _('Incorrect value in "%(field_name)s" filter') % {"field_name": label}
    )


def custom_title_filter(title, base_class=FieldListFilter):
    class CustomTitledFilter(base_class):
        def __new__(cls, *args, **kwargs):
            filter_instance = base_class.create(*args, **kwargs)
            filter_instance.title = title
            return filter_instance

    return CustomTitledFilter


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
        super().__init__(field, request, params, model, model_admin, field_path)

        filter_title = getattr(field, "_filter_title", None)
        if filter_title:
            self.title = filter_title
        elif "__" in field_path:
            self.title = "{} {}".format(field.model._meta.verbose_name, self.title)

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

    template = "admin/filters/choices_filter.html"
    _choices_list = []

    @property
    def choices_list(self):
        return self._choices_list

    @choices_list.setter
    def choices_list(self, value):
        self._choices_list = value

    def choices(self, cl):
        yield {
            "selected": False,
            "value": "",
            "display": _("All"),
            "parameter_name": self.field_path,
        }

        for lookup, title in self.choices_list:
            yield {
                "selected": smart_text(lookup) == self.value(),
                "value": lookup,
                "display": title,
                "parameter_name": self.field_path,
            }

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(**{self.field_path: self.value()})


class BooleanListFilter(ChoicesListFilter):
    _choices_list = [
        ("1", _("Yes")),
        ("0", _("No")),
    ]


class DateListFilter(BaseCustomFilter):
    """Renders filter form with date field."""

    template = "admin/filters/date_filter.html"

    def __init__(self, field, request, params, model, model_admin, field_path):
        used_parameters = {}
        self.parameter_name_start = field_path + "__start"
        self.parameter_name_end = field_path + "__end"

        for param in self.expected_parameters():
            try:
                used_parameters[param] = params.pop(param, "")
            except KeyError:
                pass
        super().__init__(field, request, params, model, model_admin, field_path)
        self.used_parameters = used_parameters

    def expected_parameters(self):
        return [self.parameter_name_start, self.parameter_name_end]

    def value(self):
        return [self.used_parameters.get(param) for param in self.expected_parameters()]

    def queryset(self, request, queryset):
        if any(self.value()):
            date = self.value()
            try:
                date_start = datetime.strptime(
                    date[0], get_format("DATE_INPUT_FORMATS")[0]
                )
                queryset = queryset.filter(
                    **{
                        "{}__gte".format(self.field_path): date_start,
                    }
                )
            except ValueError:
                pass

            try:
                date_end = datetime.strptime(
                    date[1], get_format("DATE_INPUT_FORMATS")[0]
                )
                queryset = queryset.filter(
                    **{
                        "{}__lte".format(self.field_path): date_end,
                    }
                )
            except ValueError:
                pass

            return queryset

    def choices(self, cl):
        value = self.value()
        yield {
            "parameter_name_start": self.parameter_name_start,
            "parameter_name_end": self.parameter_name_end,
            "date_start": value[0],
            "date_end": value[1],
            "date_format": date_format_to_human(get_format("DATE_INPUT_FORMATS")[0]),
        }


class VulnerabilitesByPatchDeadline(DateListFilter):
    def queryset(self, request, queryset):
        from ralph.security.models import SecurityScan

        if any(self.value()):
            filters = {}
            date_start, date_end = self.value()
            if date_start:
                filters["vulnerabilities__patch_deadline__gte"] = date_start
            if date_end:
                filters["vulnerabilities__patch_deadline__lte"] = date_end
            base_objects_ids = SecurityScan.objects.filter(**filters).values_list(
                "base_object_id", flat=True
            )
            queryset = queryset.filter(id__in=base_objects_ids)
        return queryset


class NumberListFilter(DateListFilter):
    """Renders filter form with decimal field."""

    template = "admin/filters/number_filter.html"

    def queryset(self, request, queryset):
        if any(self.value()):
            value = self.value()
            if value[0]:
                queryset = queryset.filter(
                    **{"{}__gte".format(self.field_path): value[0]}
                )
            if value[1]:
                queryset = queryset.filter(
                    **{"{}__lte".format(self.field_path): value[1]}
                )
        return queryset

    def choices(self, cl):
        value = self.value()
        # default is decimal
        step = 0.01
        if isinstance(self.field, models.IntegerField):
            step = 1

        yield {
            "parameter_name_start": self.parameter_name_start,
            "parameter_name_end": self.parameter_name_end,
            "start_value": value[0],
            "end_value": value[1],
            "step": step,
        }


class TextListFilter(BaseCustomFilter):
    """Renders filter form with char field."""

    template = "admin/filters/text_filter.html"
    separators = " or ".join(list(SEARCH_OR_SEPARATORS_REGEX.pattern[1:-1]))
    multiple = True

    def queryset(self, request, queryset):
        if self.value():
            query = Q()
            for value in SEARCH_OR_SEPARATORS_REGEX.split(self.value()):
                query |= Q(**{"{}__icontains".format(self.field_path): value.strip()})
            return queryset.filter(query)

    def choices(self, cl):
        return (
            {
                "selected": self.value(),
                "parameter_name": self.field_path,
                "separators": self.separators,
                "multiple": self.multiple,
            },
        )


class TagsListFilter(SimpleListFilter):
    title = _("Tags")
    parameter_name = "tags"
    separators = " or ".join(list(SEARCH_AND_SEPARATORS_REGEX.pattern[1:-1]))
    template = "admin/filters/text_filter.html"

    def lookups(self, request, model_admin):
        return ((1, _("Tags")),)

    def choices(self, cl):
        yield {
            "selected": self.value() or "",
            "parameter_name": self.parameter_name,
            "separators": self.separators,
            "multiple": True,
        }

    def queryset(self, request, queryset):
        if self.value():
            for value in SEARCH_AND_SEPARATORS_REGEX.split(self.value()):
                queryset = queryset.filter(tags__name=value.strip())
        return queryset


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
    empty_value = AUTOCOMPLETE_EMPTY_VALUE

    def __init__(self, field, request, params, model, model_admin, field_path):
        super().__init__(field, request, params, model, model_admin, field_path)
        self.field_model = get_model_from_relation(self.field)

    def value(self):
        value = super().value()
        return value or ""

    def queryset(self, request, queryset):
        value = self.value()
        if not value:
            ids = []
        else:
            ids = value.split(",")
        q_param = models.Q()
        for id_ in ids:
            if id_ == self.empty_value:
                q_param |= Q(**{"{}__isnull".format(self.field_path): True})
            else:
                q_param |= Q(**{self.field_path: id_})
        try:
            queryset = queryset.filter(q_param)
        except ValueError:
            _add_incorrect_value_message(request, self.title)
            raise IncorrectLookupParameters()
        # distinct for m2m
        return queryset.distinct()

    def get_related_url(self):
        return reverse(
            "admin:%s_%s_changelist"
            % (
                self.field_model._meta.app_label,
                self.field_model._meta.model_name,
            ),
        )

    def get_prefetch_data(self):
        value = self.value()
        results = {}
        if value:
            values = value.split(",")
            prepend_empty = self.empty_value in values
            queryset = self.field_model._default_manager.filter(pk__in=values)
            results = get_results(queryset, True, prepend_empty)
        return json.dumps(results)

    def choices(self, cl):
        model_options = (
            self.field_model._meta.app_label,
            self.field_model._meta.model_name,
        )
        model = get_field_by_relation_path(self.model, self.field_path).model
        widget_options = {
            "id": "id_{}".format(self.field_path),
            "query-ajax-url": reverse(
                "autocomplete-list",
                kwargs={
                    "app": model._meta.app_label,
                    "model": model.__name__,
                    "field": self.field.name,
                },
            )
            + "?prepend-empty=true",
            "multi": True,
            "detailsurl": reverse(
                "admin:{}_{}_autocomplete_details".format(*model_options)
            ),
        }
        return (
            {
                "value": self.value(),
                "attrs": flatatt(widget_options),
                "name": self.field_path,
                "related_url": self.get_related_url(),
                "search_fields_info": "Search by: {}".format(self.title),
                "prefetch_data": self.get_prefetch_data(),
            },
        )


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
        return mark_safe(level_indicator + " " + conditional_escape(smart_text(obj)))

    def queryset(self, request, queryset):
        """
        Filter in whole subtree of TreeForeignKey
        """
        if self.value():
            try:
                root = self.field.remote_field.model.objects.get(pk=self.value())
            except self.field.remote_field.model.DoesNotExist:
                _add_incorrect_value_message(request, self.title)
                raise IncorrectLookupParameters()
            else:
                queryset = queryset.filter(
                    **{
                        self.field_path + "__in": root.get_descendants(
                            include_self=True
                        )
                    }
                )
        return queryset


class TreeRelatedAutocompleteFilterWithDescendants(RelatedAutocompleteFieldListFilter):
    """
    Autocomplete filter for ForeignKeys to `mptt.models.MPTTModel` with
    filtering by object and all its descendants.
    """

    def _get_descendants(self, request, root_id):
        try:
            root = self.field.remote_field.model.objects.get(pk=root_id)
        except self.field.remote_field.model.DoesNotExist:
            _add_incorrect_value_message(request, self.title)
            raise IncorrectLookupParameters()
        return root.get_descendants(include_self=True)

    def queryset(self, request, queryset):
        value = self.value()
        if not value:
            ids = []
        else:
            ids = value.split(",")
        q_param = Q()
        for id_ in ids:
            if id_ == self.empty_value:
                q_param |= Q(**{"{}__isnull".format(self.field_path): True})
            else:
                q_param |= Q(
                    **{
                        "{}__in".format(self.field_path): self._get_descendants(
                            request, id_
                        )
                    }
                )
        try:
            queryset = queryset.filter(q_param)
        except ValueError:
            messages.warning(
                request,
                _('Incorrect value in "%(field_name)s" filter')
                % {"field_name": self.title},
            )
            raise IncorrectLookupParameters()
        return queryset


class IPFilter(SimpleListFilter):
    title = _("IP")
    parameter_name = "ip"
    template = "admin/filters/text_filter.html"

    def lookups(self, request, model_admin):
        return ((1, _("IP")),)

    def choices(self, cl):
        yield {
            "selected": self.value() or "",
            "parameter_name": self.parameter_name,
        }

    def queryset(self, request, queryset):
        if self.value():
            try:
                ipaddress.ip_address(self.value())
            except ValueError:
                _add_incorrect_value_message(request, self.title)
                raise IncorrectLookupParameters()
            else:
                queryset = queryset.filter(
                    ethernet_set__ipaddress__address=self.value()
                )
        return queryset


class MacAddressFilter(SimpleListFilter):
    title = _("MAC Address")
    parameter_name = "mac"
    template = "admin/filters/text_filter.html"

    def lookups(self, request, model_admin):
        return ((1, _("MAC Address")),)

    def queryset(self, request, queryset):
        value = self.value()
        if not value:
            return queryset

        try:
            value = MACAddressField.normalize(value)
        except ValueError:
            _add_incorrect_value_message(request, self.title)
            raise IncorrectLookupParameters()
        queryset = queryset.filter(ethernet_set__mac=value)

        return queryset

    def choices(self, cl):
        yield {
            "selected": self.value(),
            "parameter_name": self.parameter_name,
        }


class LiquidatedStatusFilter(SimpleListFilter):
    title = _("show liquidated")
    parameter_name = "liquidated"
    template = "admin/filters/checkbox_filter.html"

    def __init__(self, request, params, model, model_admin):
        super().__init__(request, params, model, model_admin)
        self.model = model

    def lookups(self, request, model_admin):
        return ((1, _("show liquidated")),)

    def choices(self, cl):
        yield {
            "selected": self.value() or False,
            "parameter_name": self.parameter_name,
        }

    def queryset(self, request, queryset):
        if not self.value():
            liquidated_status = self.model._meta.get_field(
                "status"
            ).choices.liquidated.id
            queryset = queryset.exclude(status=liquidated_status)

        return queryset


class BaseObjectHostnameFilter(SimpleListFilter):
    title = _("Hostname")
    parameter_name = "hostname"
    template = "admin/filters/text_filter.html"

    def queryset(self, request, queryset):
        if not self.value():
            return queryset
        queries = [
            Q(hostname__icontains=self.value())
            | Q(ethernet_set__ipaddress__hostname__icontains=self.value())
        ]
        return queryset.filter(*queries).distinct()

    def lookups(self, request, model_admin):
        return ((1, _("Hostname")),)

    def choices(self, cl):
        yield {
            "selected": self.value(),
            "parameter_name": self.parameter_name,
        }


def register_custom_filters():
    """
    Register custom filters for the Django admin.

    This function is called in AppConfig.ready() (ralph.admin.apps).
    """
    field_filter_mapper = [
        (lambda f: bool(f.choices), ChoicesListFilter),
        (
            lambda f: isinstance(f, (models.DecimalField, models.IntegerField)),
            NumberListFilter,
        ),
        (
            lambda f: isinstance(f, (models.BooleanField, models.NullBooleanField)),
            BooleanListFilter,
        ),
        (lambda f: isinstance(f, (models.DateField)), DateListFilter),
        (
            lambda f: isinstance(
                f, (models.CharField, models.TextField, models.IntegerField)
            ),
            TextListFilter,
        ),
        (lambda f: isinstance(f, TreeForeignKey), TreeRelatedFieldListFilter),
        (
            lambda f: (
                isinstance(f, models.ForeignKey)
                and not getattr(f, "_autocomplete", True)
            ),
            RelatedFieldListFilter,
        ),
        (
            lambda f: isinstance(f, (models.ForeignKey, models.ManyToManyField)),
            RelatedAutocompleteFieldListFilter,
        ),
        (lambda f: isinstance(f, TaggableManager), TagsListFilter),
    ]

    for func, filter_class in field_filter_mapper:
        FieldListFilter.register(func, filter_class, take_priority=True)
