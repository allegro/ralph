import logging

from django.db import models
from rest_framework import serializers

from ralph.admin.sites import ralph_site

logger = logging.getLogger("__name__")


class QuerysetRelatedMixin(object):
    """
    Allow to specify select_related and prefetch_related for queryset.

    Default select_related is taken from related admin site
    `list_select_related` attribute.
    """

    select_related = None
    prefetch_related = None
    _skip_admin_list_select_related = False

    def __init__(self, *args, **kwargs):
        self.select_related = kwargs.pop("select_related", self.select_related) or []
        self.prefetch_related = (
            kwargs.pop("prefetch_related", self.prefetch_related) or []
        )
        if getattr(self, "queryset", None) is not None:
            admin_site = ralph_site._registry.get(self.queryset.model)
            if (
                admin_site
                and not self._skip_admin_list_select_related
                and admin_site.list_select_related
            ):
                self.select_related.extend(admin_site.list_select_related)
        super().__init__(*args, **kwargs)

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.select_related:
            queryset = queryset.select_related(*self.select_related)
        if self.prefetch_related:
            queryset = queryset.prefetch_related(*self.prefetch_related)
        return queryset


class PolymorphicViewSetMixin(QuerysetRelatedMixin):
    """
    ViewSet for polymorphic models - for each descendant model, dedicated
    serializer for this model is used. This ViewSet is working together with
    `PolymorphicSerializer`.
    """

    def get_queryset(self):
        queryset = super().get_queryset()
        polymorphic_select_related = {}
        polymorphic_prefetch_related = {}
        for model, view in self._viewsets_registry.items():
            if model in queryset.model._polymorphic_descendants:
                polymorphic_select_related[model._meta.object_name] = (
                    view.select_related
                )
                polymorphic_prefetch_related[model._meta.object_name] = (
                    view.prefetch_related
                )
        return queryset.polymorphic_select_related(
            **polymorphic_select_related
        ).polymorphic_prefetch_related(**polymorphic_prefetch_related)

    def get_serializer(self, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        kwargs["context"] = self.get_serializer_context()
        # for single object use dedicated serializer directly
        # for many objects, `PolymorphicListSerializer` is used underneath
        if not kwargs.get("many"):
            try:
                serializer_class = serializer_class._serializers_registry[
                    args[0].__class__
                ]
            except KeyError:
                logger.warning(
                    "Dedicated serializer not found for %s", args[0].__class__
                )
        return serializer_class(*args, **kwargs)


class PolymorphicListSerializer(serializers.ListSerializer):
    """
    List serializer to use with many `Polymorphic` instances.
    For each instance (model) dedicated `to_representation` of this model
    serializer is called.
    """

    def __init__(self, *args, **kwargs):
        self.child_serializers = kwargs.pop("child_serializers")
        super().__init__(*args, **kwargs)

    def to_representation(self, data):
        iterable = data.all() if isinstance(data, models.Manager) else data

        def iterate():
            for item in iterable:
                if self.child_serializers.get(item.__class__):
                    yield self.child_serializers[item.__class__].to_representation(item)
                else:
                    try:
                        yield {"id": item.id}
                    except Exception:
                        yield {}

        return [i for i in iterate()]


class PolymorphicSerializer(serializers.Serializer):
    """
    Serializer to user with `Polymorphic` model.

    The only difference comparing to regular serializer is case with many
    objects - instead of `ListSerializer`, `PolymorphicListSerializer` is used.
    """

    @classmethod
    def many_init(cls, *args, **kwargs):
        child_serializer = cls(*args, **kwargs)
        # use dedicated model serializer for each possible descendant class
        # and pass it to list serializer
        child_serializers = {}
        for descendant_model in cls.Meta.model._polymorphic_descendants:
            child_serializers[descendant_model] = cls._serializers_registry.get(
                descendant_model, cls
            )(*args, **kwargs)
        list_kwargs = {
            "child": child_serializer,
            "child_serializers": child_serializers,
        }
        list_kwargs.update(
            dict(
                [
                    (key, value)
                    for key, value in kwargs.items()
                    if key in serializers.LIST_SERIALIZER_KWARGS
                ]
            )
        )
        return PolymorphicListSerializer(*args, **list_kwargs)
