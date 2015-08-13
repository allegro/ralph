import operator
from functools import reduce

from django.conf.urls import url
from django.db.models import Q
from django.http import Http404, HttpResponseBadRequest, JsonResponse
from django.views.generic import View

from ralph.admin.helpers import get_admin_url
from ralph.admin.sites import ralph_site
from ralph.lib.permissions.models import PermissionsForObjectMixin

QUERY_PARAM = 'q'
DETAIL_PARAM = 'pk'


class JsonViewMixin(object):
    """
    A mixin that can be used to render a JSON response.
    """
    def render_to_json_response(self, context, **response_kwargs):
        """
        Returns a JSON response, transforming 'context' to make the payload.
        """
        return JsonResponse(context, **response_kwargs)


class SuggestView(JsonViewMixin, View):
    """
    Base class for list and detail view.
    """
    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        """
        Returns serialized dict as JSON object.
        """
        can_edit = ralph_site._registry[self.model].has_change_permission(
            self.request
        )
        results = [
            {
                'pk': obj.pk,
                '__str__': str(obj),
                'edit_url': get_admin_url(obj, 'change') if can_edit else None,
            } for obj in self.get_queryset(request.user)
        ]
        return self.render_to_json_response({'results': results})


class AjaxAutocompleteMixin(object):
    """
    This mixin added new endpoint to admin's urls for autocomplete mechanism.
    """
    def get_urls(self):
        urls = super().get_urls()
        outer_model = self.model
        search_fields = self.search_fields
        ordering = self.ordering or ()

        class List(SuggestView):
            limit = 10
            model = outer_model

            def dispatch(self, request, *args, **kwargs):
                self.query = request.GET.get(QUERY_PARAM, None)
                if not self.query:
                    return HttpResponseBadRequest()
                return super().dispatch(request, *args, **kwargs)

            def get_queryset(self, user):
                queryset = self.model._default_manager.all()
                if self.query:
                    qs = [
                        Q(**{'{}__icontains'.format(field): self.query})
                        for field in search_fields
                    ]
                    queryset = queryset.filter(reduce(operator.or_, qs))
                if issubclass(self.model, PermissionsForObjectMixin):
                    queryset = self.model._get_objects_for_user(user, queryset)
                return queryset.order_by(*ordering)[:self.limit]

        class Detail(SuggestView):
            model = outer_model

            def dispatch(self, request, *args, **kwargs):
                self.pk = request.GET.get(DETAIL_PARAM, None)
                if not self.pk:
                    return HttpResponseBadRequest()
                return super().dispatch(request, *args, **kwargs)

            def get_queryset(self, user):
                queryset = self.model.objects.filter(pk=int(self.pk))
                if issubclass(self.model, PermissionsForObjectMixin):
                    queryset = self.model._get_objects_for_user(user, queryset)
                if not queryset.exists():
                    raise Http404
                return queryset

        params = outer_model._meta.app_label, outer_model._meta.model_name

        my_urls = [
            url(
                r'^autocomplete/suggest/$',
                List.as_view(),
                name='{}_{}_autocomplete_suggest'.format(*params)
            ),
            url(
                r'^autocomplete/details/$',
                Detail.as_view(),
                name='{}_{}_autocomplete_details'.format(*params)
            ),
        ]
        return my_urls + urls
