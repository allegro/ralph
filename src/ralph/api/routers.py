# -*- coding: utf-8 -*-
from collections import OrderedDict

from django.urls import NoReverseMatch
from rest_framework import routers
from rest_framework.response import Response
from rest_framework.reverse import reverse

from ralph.lib.custom_fields.api.routers import NestedCustomFieldsRouterMixin
from ralph.lib.permissions.api import RalphPermission


class RalphRouter(NestedCustomFieldsRouterMixin, routers.DefaultRouter):
    """
    Acts like DefaultRouter + checks if user has permissions to see viewset.
    Viewsets for which user doesn't have permissions are hidden in root view.
    """

    # skip .json style formatting suffixes in urls
    include_format_suffixes = False

    def get_api_root_view(self, api_urls=None):
        api_root_dict = {}
        list_name = self.routes[0].name
        for prefix, viewset, basename in self.registry:
            api_root_dict[prefix] = (list_name.format(basename=basename), viewset)
        # present resources in alphabetical order (sort by key, which is url)
        api_root_dict = OrderedDict(sorted(api_root_dict.items()))
        from rest_framework import views

        class APIRoot(views.APIView):
            _ignore_model_permissions = True

            def _check_viewset_permissions(self, request, viewset):
                return RalphPermission().has_permission(request, viewset)

            def get(self, request, *args, **kwargs):
                ret = OrderedDict()
                namespace = request.resolver_match.namespace
                for key, (url_name, viewset) in api_root_dict.items():
                    if not self._check_viewset_permissions(request, viewset):
                        continue
                    if namespace:
                        url_name = namespace + ":" + url_name
                    try:
                        ret[key] = reverse(
                            url_name,
                            args=args,
                            kwargs=kwargs,
                            request=request,
                            format=kwargs.get("format", None),
                        )
                    except NoReverseMatch:
                        continue

                return Response(ret)

        return APIRoot.as_view()


router = RalphRouter()
