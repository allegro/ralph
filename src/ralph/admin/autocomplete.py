import operator
import re
from functools import reduce

from django.conf.urls import url
from django.db.models import Q
from django.db.models.loading import get_model
from django.http import Http404, HttpResponseBadRequest, JsonResponse
from django.views.generic import View

from ralph.admin.helpers import get_admin_url
from ralph.admin.sites import ralph_site
from ralph.lib.permissions.models import PermissionsForObjectMixin

QUERY_PARAM = 'q'
DETAIL_PARAM = 'pk'
QUERY_REGEX = re.compile(r'[.| ]')


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
        empty_element = '<i class="empty">&lt;empty&gt;</i>'
        tooltip = ''
        for field in self.autocomplete_tooltip_fields:
            if not hasattr(self, field):
                continue
            value = getattr(self, field)
            label = str(self._meta.get_field(field).verbose_name)
            tooltip += '<strong>{}:</strong>&nbsp;{}<br>'.format(
                label.capitalize(), value or empty_element
            )
        return tooltip


class SuggestView(JsonViewMixin, View):
    """
    Base class for list and detail view.
    """
    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        """
        Returns serialized dict as JSON object.
        """
        # TODO
        # Add in the future redirected to the model that is being edited
        can_edit = ralph_site._registry[self.model].has_change_permission(
            self.request
        )
        results = [
            {
                'pk': obj.pk,
                '__str__': str(obj),
                'label': getattr(obj, 'autocomplete_str', None),
                'edit_url': '{}?_popup=1'.format(
                    get_admin_url(obj, 'change')
                ) if can_edit else None,
                'tooltip': getattr(obj, 'autocomplete_tooltip', None)
            } for obj in self.get_queryset(request.user)
        ]
        return self.render_to_json_response({'results': results})


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
            model = outer_model

            def dispatch(self, request, *args, **kwargs):
                self.pk = request.GET.get(DETAIL_PARAM, None)
                if not self.pk:
                    return HttpResponseBadRequest()
                self.pks = self.pk.split(',')
                return super().dispatch(request, *args, **kwargs)

            def get_queryset(self, user):
                queryset = self.model._default_manager.filter(pk__in=self.pks)
                if issubclass(self.model, PermissionsForObjectMixin):
                    queryset = self.model._get_objects_for_user(user, queryset)
                if not queryset.exists():
                    raise Http404
                return queryset

        params = outer_model._meta.app_label, outer_model._meta.model_name

        my_urls = [
            url(
                r'^autocomplete/details/$',
                Detail.as_view(),
                name='{}_{}_autocomplete_details'.format(*params)
            ),
        ]
        return my_urls + urls


class AutocompleteList(SuggestView):
    limit = 10
    model = None

    def dispatch(self, request, *args, **kwargs):
        try:
            model = get_model(kwargs['app'], kwargs['model'])
        except LookupError:
            return HttpResponseBadRequest('Model not found')

        self.field = model._meta.get_field(kwargs['field'])
        self.model = self.field.rel.to
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
        split_by_words = getattr(self.model, 'autocomplete_words_split', False)
        if split_by_words:
            for value in QUERY_REGEX.split(query):
                if value:
                    query_filters = [
                        Q(**{'{}__icontains'.format(field): value})
                        for field in search_fields
                    ]
                    queryset = queryset.filter(
                        reduce(operator.or_, query_filters)
                    )
        else:
            query_filters = [
                Q(**{'{}__icontains'.format(field): query})
                for field in search_fields
            ]
            queryset = queryset.filter(reduce(operator.or_, query_filters))
        return queryset

    def get_base_ids(self, model, value):
        """
        Return IDs for related models.
        """
        search_fields = ralph_site._registry[model].search_fields
        if not search_fields:
            return []

        queryset = getattr(
            model,
            'get_autocomplete_queryset',
            model._default_manager.all
        )()
        if issubclass(model, PermissionsForObjectMixin):
            queryset = model._get_objects_for_user(
                self.request.user, queryset
            )
        queryset = self.get_query_filters(queryset, value, search_fields)
        return queryset[:self.limit].values_list('pk', flat=True)

    def get_queryset(self, user):
        search_fields = ralph_site._registry[self.model].search_fields
        queryset = getattr(
            self.model,
            'get_autocomplete_queryset',
            self.model._default_manager.all
        )()
        polymorphic_descendants = getattr(
            self.model, '_polymorphic_descendants', []
        )
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
                id_list.extend(self.get_base_ids(
                    related_model,
                    self.query,
                ))
            queryset = queryset.filter(pk__in=id_list)
        else:
            if self.query:
                queryset = self.get_query_filters(
                    queryset, self.query, search_fields
                )
            if issubclass(self.model, PermissionsForObjectMixin):
                queryset = self.model._get_objects_for_user(
                    user, queryset
                )
        return queryset[:self.limit]
