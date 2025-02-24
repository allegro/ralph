import logging
import operator
import re
from functools import reduce

from dj.choices import Choices
from django.apps import apps
from django.conf.urls import url
from django.core.exceptions import FieldDoesNotExist
from django.db.models import Manager, Q
from django.http import Http404, HttpResponseBadRequest, JsonResponse
from django.views.generic import View

from ralph.admin.helpers import (
    get_admin_url,
    get_field_by_relation_path,
    get_value_by_relation_path
)
from ralph.admin.sites import ralph_site
from ralph.lib.permissions.models import PermissionsForObjectMixin

AUTOCOMPLETE_EMPTY_VALUE = "0"
AUTOCOMPLETE_EMPTY_LABEL = '<i class="empty">empty</i>'
QUERY_PARAM = "q"
DETAIL_PARAM = "pk"
QUERY_REGEX = re.compile(r"[.| ]")

logger = logging.getLogger(__name__)


def get_results(queryset, can_edit, prepend_empty=False):
    results = []
    if prepend_empty:
        results.append(
            {
                "pk": AUTOCOMPLETE_EMPTY_VALUE,
                "__str__": AUTOCOMPLETE_EMPTY_LABEL,
            }
        )
    results.extend(
        [
            {
                "pk": obj.pk,
                "__str__": getattr(obj, "autocomplete_str", str(obj)),
                "edit_url": "{}?_popup=1".format(get_admin_url(obj, "change"))
                if can_edit
                else None,
                "tooltip": getattr(obj, "autocomplete_tooltip", None),
            }
            for obj in queryset
        ]
    )
    return results


class JsonViewMixin(object):
    """
    A mixin that can be used to render a JSON response.
    """

    def render_to_json_response(self, context, **response_kwargs):
        """
        Returns a JSON response, transforming 'context' to make the payload.
        """
        return JsonResponse(context, **response_kwargs)


class AutocompleteTooltipMixin(object):
    autocomplete_tooltip_fields = []

    @property
    def autocomplete_tooltip(self):
        empty_element = "<empty>"
        tooltip = []
        for field in self.autocomplete_tooltip_fields:
            try:
                model_field = get_field_by_relation_path(self, field)
            except FieldDoesNotExist:
                logger.warning(
                    "Autocomplete tooltip field %s not found for %s",
                    field,
                    self._meta.model_name,
                )
                continue
            value = get_value_by_relation_path(self, field)
            if isinstance(model_field.choices, Choices):
                value = model_field.choices.name_from_id(value)
            label = str(model_field.verbose_name)
            if isinstance(value, Manager):
                value = ", ".join(map(str, value.all()))
            tooltip.append("{}: {}".format(label.capitalize(), value or empty_element))
        return "\n".join(tooltip)


class SuggestView(JsonViewMixin, View):
    """
    Base class for list and detail view.
    """

    http_method_names = ["get"]

    def get_results(self, user, can_edit, prepend_empty=False):
        return get_results(self.get_queryset(user), can_edit, prepend_empty)

    def get(self, request, *args, **kwargs):
        """
        Returns serialized dict as JSON object.
        """
        # TODO
        # Add in the future redirected to the model that is being edited
        can_edit = ralph_site._registry[self.model].has_change_permission(self.request)
        results = self.get_results(request.user, can_edit)
        return self.render_to_json_response({"results": results})


class AjaxAutocompleteMixin(object):
    """
    This mixin added new endpoint to admin's urls for autocomplete mechanism.
    """

    def get_autocomplete_queryset(self):
        return self.model._default_manager.all()

    def get_urls(self):
        urls = super().get_urls()
        outer_model = self.model

        class Detail(SuggestView):
            empty_value = AUTOCOMPLETE_EMPTY_VALUE
            model = outer_model

            def dispatch(self, request, *args, **kwargs):
                self.pk = request.GET.get(DETAIL_PARAM, None)
                if not self.pk:
                    return HttpResponseBadRequest()
                self.values = self.pk.split(",")
                return super().dispatch(request, *args, **kwargs)

            def get_results(self, user, can_edit):
                prepend_empty = self.empty_value in self.values
                results = super().get_results(user, can_edit, prepend_empty)
                return results

            def get_queryset(self, user):
                queryset = self.model._default_manager.filter(pk__in=self.values)
                if issubclass(self.model, PermissionsForObjectMixin):
                    queryset = self.model._get_objects_for_user(user, queryset)
                if self.values != [self.empty_value] and not queryset.exists():
                    raise Http404
                return queryset

        params = outer_model._meta.app_label, outer_model._meta.model_name
        my_urls = [
            url(
                r"^autocomplete/details/$",
                Detail.as_view(),
                name="{}_{}_autocomplete_details".format(*params),
            ),
        ]
        return my_urls + urls


class AutocompleteList(SuggestView):
    empty_value = AUTOCOMPLETE_EMPTY_VALUE
    limit = 10
    model = None

    def dispatch(self, request, *args, **kwargs):
        try:
            model = apps.get_model(kwargs["app"], kwargs["model"])
        except LookupError:
            return HttpResponseBadRequest("Model not found")

        self.field = model._meta.get_field(kwargs["field"])
        self.model = self.field.remote_field.model
        self.query = request.GET.get(QUERY_PARAM, None)
        if not self.query:
            return HttpResponseBadRequest()
        return super().dispatch(request, *args, **kwargs)

    def get_query_filters(self, queryset, query, search_fields):
        """
        Get query filters to Django queryset filter.

        Args:
            queryset: Django queryset
            query: Query string
            search_fields: List of fields

        Returns:
            Django queryset
        """
        split_by_words = getattr(self.model, "autocomplete_words_split", False)
        if split_by_words:
            for value in QUERY_REGEX.split(query):
                if value:
                    query_filters = [
                        Q(**{"{}__icontains".format(field): value})
                        for field in search_fields
                    ]
                    if query_filters:
                        queryset = queryset.filter(reduce(operator.or_, query_filters))
        else:
            query_filters = [
                Q(**{"{}__icontains".format(field): query}) for field in search_fields
            ]
            if query_filters:
                queryset = queryset.filter(reduce(operator.or_, query_filters))
        return queryset

    def get_base_ids(self, model, value):
        """
        Return IDs for related models.
        """
        # TODO: what if search_fileds are empty
        search_fields = ralph_site._registry[model].search_fields
        if not search_fields:
            return []

        queryset = getattr(
            model, "get_autocomplete_queryset", model._default_manager.all
        )()
        if issubclass(model, PermissionsForObjectMixin):
            queryset = model._get_objects_for_user(self.request.user, queryset)
        queryset = self.get_query_filters(queryset, value, search_fields)
        return queryset[: self.limit].values_list("pk", flat=True)

    def get_results(self, user, can_edit):
        prepend_empty = self.request.GET.get("prepend-empty", 0) == "true"
        results = super().get_results(user, can_edit, prepend_empty)
        return results

    def get_queryset(self, user):
        search_fields = ralph_site._registry[self.model].search_fields
        queryset = getattr(
            self.model, "get_autocomplete_queryset", self.model._default_manager.all
        )()
        polymorphic_descendants = getattr(self.model, "_polymorphic_descendants", [])
        limit_choices = self.field.get_limit_choices_to()
        if limit_choices:
            queryset = queryset.filter(**limit_choices)
            try:
                polymorphic_descendants = self.field.get_limit_models()
            except AttributeError:
                pass

        if polymorphic_descendants:
            id_list = []
            for related_model in polymorphic_descendants:
                id_list.extend(
                    self.get_base_ids(
                        related_model,
                        self.query,
                    )
                )
            queryset = queryset.filter(pk__in=id_list)
        else:
            if self.query:
                queryset = self.get_query_filters(queryset, self.query, search_fields)
            if issubclass(self.model, PermissionsForObjectMixin):
                queryset = self.model._get_objects_for_user(user, queryset)
        queryset = queryset.distinct()
        return queryset[: self.limit]
