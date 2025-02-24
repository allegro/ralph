import inspect
import logging
import operator
from functools import reduce

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import FieldDoesNotExist
from django.db import models
from django.forms import Widget
from django_filters import Filter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import BaseFilterBackend

from ralph.admin.helpers import get_field_by_relation_path
from ralph.admin.sites import ralph_site
from ralph.data_importer.models import ImportedObjects
from ralph.lib.mixins.models import TaggableMixin

logger = logging.getLogger(__name__)

TRUE_VALUES = dict.fromkeys([1, "1", "true", "True", "yes"], True)
FALSE_VALUES = dict.fromkeys([0, "0", "false", "False", "no"], False)
BOOL_VALUES = TRUE_VALUES.copy()
BOOL_VALUES.update(FALSE_VALUES)


class BooleanWidget(Widget):
    def value_from_datadict(self, data, files, name):
        value = data.get(name, None)
        return BOOL_VALUES.get(value, None)


class BooleanFilter(Filter):
    def __init__(self, widget=None, *args, **kwargs):
        widget = widget or BooleanWidget
        super().__init__(widget=widget, *args, **kwargs)


class AdditionalDjangoFilterBackend(DjangoFilterBackend):
    """
    Allows to spcify additional FilterSet for viewset (besides standard one,
    which uses fields from `filter_fields` property.
    """

    def get_filter_class(self, view, queryset=None):
        return getattr(view, "additional_filter_class", None)


class TagsFilterBackend(BaseFilterBackend):
    """
    Filter queryset by tags. Multiple tags could be specified in url query:
    `<URL>?tag=abc&tag=def&tag=123`.
    """

    def _handle_tags_filter(self, queryset, tags):
        query = models.Q()
        for tag in tags:
            query &= models.Q(tags__name=tag)
        queryset = queryset.filter(query)
        return queryset

    def filter_queryset(self, request, queryset, view):
        tags = request.query_params.getlist("tag")
        if tags and issubclass(queryset.model, TaggableMixin):
            queryset = self._handle_tags_filter(queryset, tags)
        return queryset


class ImportedIdFilterBackend(BaseFilterBackend):
    """
    Filter by imported object id
    """

    def filter_queryset(self, request, queryset, view):
        for param_name, field_name, use_content_type in [
            ("_imported_object_id", "old_object_pk", True),
            ("_ralph2_ci_uid", "old_ci_uid", False),
            ("_ralph2_ci_uid__startswith", "old_ci_uid__startswith", False),
        ]:
            param_value = request.query_params.get(param_name)
            if param_value:
                logger.debug(
                    "Processing imported id query param {}:{}".format(
                        param_name, param_value
                    )
                )
                query_params = {field_name: param_value}
                if use_content_type:
                    query_params["content_type"] = ContentType.objects.get_for_model(  # noqa
                        queryset.model
                    )
                logger.debug("Filtering imported object by {}".format(query_params))
                try:
                    imported_objects_pks = ImportedObjects.objects.filter(
                        **query_params
                    ).values_list("object_pk", flat=True)
                except ImportedObjects.DoesNotExist:
                    return queryset.model.objects.none()
                else:
                    queryset = queryset.filter(pk__in=imported_objects_pks)
        return queryset


class ExtendedFiltersBackend(BaseFilterBackend):
    """
    Apply filters defined by extended filters in view (usefull in Polymorphic
    objects).

    For example, when
    `view.extended_filter_fields = {'name': ['asset__hostname', 'ip__address']}`
    using `name` filter (query param), `asset_hostname` and `ip_address` will
    be filtered by.
    """

    def _handle_extended_filters(self, request, queryset, extended_filter_fields):
        for field, field_filters in extended_filter_fields.items():
            value = request.query_params.get(field, None)
            if value:
                q_param = models.Q()
                for field_name in field_filters:
                    q_param |= models.Q(**{field_name: value})
                queryset = queryset.filter(q_param)
        return queryset

    def filter_queryset(self, request, queryset, view):
        """
        Resolve extended filters
        """
        extended_filter_fields = getattr(view, "extended_filter_fields", {})
        if extended_filter_fields:
            logger.debug("Applying ExtendedFiltersBackend filters")
            queryset = self._handle_extended_filters(
                request, queryset, extended_filter_fields
            )
        return queryset


class LookupFilterBackend(BaseFilterBackend):
    """
    Filter by lookups (using Django's __ convention) in query params.

    This filter supports also lookups in extended filters.
    """

    # allowed lookups depending on field type (using Django's __ convention)
    # for other types of fields, only strict lookup is allowed
    field_type_lookups = {
        # TODO: in and range filters are not working (some iterable is required)
        models.IntegerField: {
            "lte",
            "gte",
            "lt",
            "gt",
            "exact",
            "in",
            "range",
            "isnull",
        },
        models.CharField: {
            "startswith",
            "istartswith",
            "endswith",
            "icontains",
            "contains",
            "in",
            "iendswith",
            "isnull",
            "regex",
            "iregex",
        },
        models.DateField: {
            "year",
            "month",
            "day",
            "week_day",
            "range",
            "isnull",
            "lte",
            "gte",
            "lt",
            "gt",
        },
        models.DateTimeField: {
            "year",
            "month",
            "day",
            "week_day",
            "hour",
            "minute",
            "second",
            "range",
            "isnull",
            "lte",
            "gte",
            "lt",
            "gt",
        },
        models.DecimalField: {
            "lte",
            "gte",
            "lt",
            "gt",
            "exact",
            "in",
            "range",
            "isnull",
        },
        models.AutoField: {"startswith", "exact"},
    }

    def _validate_single_query_lookup(self, model, model_field_name, lookup, value):
        """
        Validate single query param lookup.

        Args:
            model: Django model
            model_field_name: name of model field extracted from field_name
            lookup: name of lookup (ex. `startswith')
            value: value to look for

        Returns: dict with filter params (containing eiter 0 or 1 elem). Result
            is not empty if lookup for field is valid. Result is empty when
            field path is not valid or lookup for field is not valid.
        """
        result = {}
        logger.debug(
            "Validating {}__{} lookup for model {}; value: {}".format(
                model_field_name, lookup, model, value
            )
        )
        try:
            model_field = get_field_by_relation_path(model, model_field_name)
        except FieldDoesNotExist:
            logger.debug("{} not found for model {}".format(model_field_name, model))
        else:
            field_lookups = set()
            # process every class from which field is inheriting
            for cl in inspect.getmro(model_field.__class__):
                field_lookups |= self.field_type_lookups.get(cl, set())
            logger.debug(
                "Available lookups for {}.{} : {}".format(
                    model, model_field_name, field_lookups
                )
            )
            if lookup in field_lookups:
                if lookup == "isnull":
                    if value not in BOOL_VALUES:
                        logger.debug(
                            "Unknown value for isnull filter: {}".format(value)
                        )
                        return {}
                    else:
                        value = BOOL_VALUES[value]
                result = {"{}__{}".format(model_field_name, lookup): value}
        return result

    def _validate_query_lookups(
        self, model, request, filter_fields, extended_filter_fields
    ):
        """
        Validates all lookups from query params.

        Args:
            model: Django model
            request: current request
            filter_fields: list of fields available for filtering (ex. ['name'])
            extended_filter_fields: dict with extended filters for single field
                name, ex. `{'name': ['asset__hostname', 'ip__address']}`.
                Usefull especially with polymorphic models (when searching by
                field `name` could be later expanded to filter by many fields
                in descendants models)

        Returns: 2-element tuple with:
            * list with positional filters (using Q objects)
            * dict with keywords filters
        """
        result = []
        kw_result = {}
        logger.debug(
            "Processing {} filters with filter fields={} and extended filter "
            "fields={}".format(model, filter_fields, extended_filter_fields)
        )
        for field_name, value in request.query_params.items():
            logger.debug("Processing query param {}:{}".format(field_name, value))
            model_field_name, _, lookup = field_name.rpartition("__")

            # try if this field search could be expanded to other fields
            extended_filters = {}
            for extended_field_name in extended_filter_fields.get(model_field_name, []):
                extended_filters.update(
                    self._validate_single_query_lookup(
                        model, extended_field_name, lookup, value
                    )
                )
            if extended_filters:
                logger.debug(
                    "Using {} extended filters for query {}:{}".format(
                        extended_filters, field_name, value
                    )
                )
                result.append(
                    reduce(
                        operator.or_,
                        [models.Q(**{k: v}) for k, v in extended_filters.items()],
                    )
                )

            # skip if field is not available to filter for
            if model_field_name in filter_fields:
                filters = self._validate_single_query_lookup(
                    model, model_field_name, lookup, value
                )
                logger.debug(
                    "Using {} filters for query {}:{}".format(
                        filters, field_name, value
                    )
                )
                kw_result.update(filters)
        return result, kw_result

    def filter_queryset(self, request, queryset, view):
        lookups, kw_lookups = self._validate_query_lookups(
            queryset.model,
            request,
            view.filter_fields,
            getattr(view, "extended_filter_fields", {}),
        )
        if lookups or kw_lookups:
            logger.debug("Applying LookupFilterBackend filters")
            queryset = queryset.filter(*lookups, **kw_lookups)
        return queryset


class PolymorphicDescendantsFilterBackend(LookupFilterBackend):
    """
    Filter descendants of polymorphic models (especially by extended filters).
    """

    def _process_model(self, model, request, filter_fields, extended_filter_fields):
        ids = set()
        is_lookup_used = False
        lookups, kw_lookups = self._validate_query_lookups(
            model, request, filter_fields, extended_filter_fields
        )
        if lookups or kw_lookups:
            is_lookup_used = True
            ids = set(
                model.objects.filter(*lookups, **kw_lookups).values_list(
                    "pk", flat=True
                )
            )
        return ids, is_lookup_used

    def _get_polymorphic_ids(self, base_model, polymorphic_models, request, view):
        """
        Returns ids of polymorphic objects based on query filters.

        Args:
            base_model: (polymorphic) parent model
            polymorphic_models: list of models to consider (descendants of
                base model)
            request: current request
            view: current view

        Returns: tuple (
            * set of ids,
            * True if at least one of the lookups was applied
        )
        """
        ids = set()
        is_lookup_used = False

        # process base model
        # used only with extended filters
        model_ids, model_is_lookup_used = self._process_model(
            base_model,
            request,
            view.filter_fields,
            getattr(view, "extended_filter_fields", {}),
        )
        ids |= model_ids
        is_lookup_used |= model_is_lookup_used
        for model in polymorphic_models:
            filter_fields = []
            model_viewset = view._viewsets_registry.get(model)
            if model_viewset:
                # get filters which are applicable to descdenant type
                filter_fields = getattr(model_viewset, "filter_fields", [])
            if not filter_fields:
                # if not filter_fields from API viewset get fields
                # from django model admin
                filter_fields = ralph_site._registry[model].search_fields

            model_ids, model_is_lookup_used = self._process_model(
                model, request, filter_fields, {}
            )
            ids |= model_ids
            is_lookup_used |= model_is_lookup_used
        return ids, is_lookup_used

    def filter_queryset(self, request, queryset, view):
        polymorphic_descendants = getattr(
            queryset.model, "_polymorphic_descendants", []
        )
        if polymorphic_descendants:
            ids, is_lookup_used = self._get_polymorphic_ids(
                queryset.model, polymorphic_descendants, request, view
            )
            if is_lookup_used:
                logger.debug("Applying PolymorphicDescendantsFilterBackend filters")
                queryset = queryset.filter(pk__in=list(ids))
        return queryset
