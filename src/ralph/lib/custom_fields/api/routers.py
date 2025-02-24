from django.conf.urls import include, url
from rest_framework import routers
from rest_framework_nested.routers import NestedSimpleRouter


class NestedCustomFieldsRouterMixin(object):
    """
    Mixin to handle nested resources for custom fields in API.

    Custom fields values are presented in context of object to which they are
    attached. To achieve that, nested resource for particular object is created,
    ex. /api/<somemodel>/<somemodel_pk>/customfields
    """
    # URL path used to build nested resource for customfields
    nested_resource_prefix = r'customfields'
    # name of nested resource for customfields, used by DRF (ex. to reverse URL)
    nested_resource_basename = '{}-customfields'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.nested_registry = []

    def register(self, prefix, viewset, basename=None):
        super().register(prefix, viewset, basename=basename)
        if basename is None:
            basename = self.get_default_basename(viewset)
        from .serializers import WithCustomFieldsSerializerMixin
        if (
            issubclass(
                viewset.serializer_class, WithCustomFieldsSerializerMixin
            ) and
            getattr(viewset, '_nested_custom_fields', True)
        ):
            # additionally, registed nested resource for custom fields
            self._attach_nested_custom_fields(prefix, viewset, basename)

    def _attach_nested_custom_fields(self, prefix, viewset, basename):
        """
        Creates dedicated viewset for nested customfields in context of
        particular model.
        """
        # cyclic imports, meh
        from ralph.api.viewsets import RalphAPIViewSet

        from .viewsets import ObjectCustomFieldsViewSet
        model = viewset.queryset.model
        custom_fields_related_viewset = type(
            '{}CustomFieldsViewSet'.format(model._meta.object_name),
            (ObjectCustomFieldsViewSet, RalphAPIViewSet),
            {'related_model': model}
        )
        # notice that, although it's custom fields (nested) resource,
        # for every model separated (nested) router is created!
        nested_router = NestedSimpleRouter(
            self,
            prefix,
            lookup=custom_fields_related_viewset.related_model_router_lookup
        )
        nested_router.register(
            self.nested_resource_prefix,
            custom_fields_related_viewset,
            basename=self.nested_resource_basename.format(basename),
        )
        self.nested_registry.append(nested_router)

    def get_urls(self):
        urls = super().get_urls()
        # additionally, return nested routers urls too
        for nr in self.nested_registry:
            urls.append(url(r'^', include(nr.urls)))
        return urls


class NestedCustomFieldsRouter(
    NestedCustomFieldsRouterMixin, routers.DefaultRouter
):
    pass
