# -*- coding: utf-8 -*-
import logging
from collections import OrderedDict

from rest_framework import permissions, relations, serializers
from taggit_serializer.serializers import (
    TaggitSerializer,
    TagListSerializerField
)

from ralph.api.relations import RalphHyperlinkedRelatedField, RalphRelatedField
from ralph.lib.mixins.models import TaggableMixin
from ralph.lib.permissions.api import (
    PermissionsPerFieldSerializerMixin,
    RelatedObjectsPermissionsSerializerMixin
)

logger = logging.getLogger(__name__)


class ReversedChoiceField(serializers.ChoiceField):
    """
    Choice field serializer which allow to pass value by name instead of key.
    Additionally it present value in user-friendly format by-name.

    Notice that requirement for this field to work properly is uniqueness of
    choice values.

    This field works perfectly with `dj.choices.Choices`.
    """
    def __init__(self, choices, **kwargs):
        super(ReversedChoiceField, self).__init__(choices, **kwargs)
        # mapping by value
        self.reversed_choices = OrderedDict([(v, k) for (k, v) in choices])

    def to_representation(self, obj):
        """
        Return choice name (value) instead of default key.
        """
        try:
            return self.choices[obj]
        except KeyError:
            return super().to_representation(obj)

    def to_internal_value(self, data):
        """
        Try to get choice by value first. If it doesn't succeed fallback to
        default action (get by key).
        """
        try:
            return self.reversed_choices[data]
        except KeyError:
            pass
        return super(ReversedChoiceField, self).to_internal_value(data)


class DeclaredFieldsMetaclass(serializers.SerializerMetaclass):
    """
    Add additional declared fields in specific cases.

    When serializer's model inherits from
    `ralph.lib.mixins.models.TaggableMixin`, tags field is attached.
    """
    def __new__(cls, name, bases, attrs):
        model = getattr(attrs.get('Meta'), 'model', None)
        if model and issubclass(model, TaggableMixin):
            attrs['tags'] = TagListSerializerField(required=False)
            attrs['prefetch_related'] = (
                list(attrs.get('prefetch_related', [])) + ['tags']
            )
        return super().__new__(cls, name, bases, attrs)


class RalphAPISerializerMixin(
    TaggitSerializer,
    RelatedObjectsPermissionsSerializerMixin,
    PermissionsPerFieldSerializerMixin,
    metaclass=DeclaredFieldsMetaclass
):
    """
    Mix used in Ralph API serializers features:
        * checking if user has permissions to related objects (through
          `RelatedObjectsPermissionsSerializerMixin`)
        * handling field-level permissions (through
          `PermissionsPerFieldSerializerMixin`)
        * use `ReversedChoiceField` as default serializer for choice field
        * request and user object easily accessible in each related serializer
    """
    serializer_choice_field = ReversedChoiceField

    @property
    def serializer_related_field(self):
        """
        When it's safe request (ex. GET), related serailizer is hyperlinked
        (contains url to related object). When it's not safe request (ex. POST),
        serializer expect to pass only PK for related object.
        """
        if self.context['request'].method in permissions.SAFE_METHODS:
            return RalphHyperlinkedRelatedField
        return RalphRelatedField

    def get_default_field_names(self, declared_fields, model_info):
        """
        Return the default list of field names that will be used if the
        `Meta.fields` option is not specified.

        Add additional pk field at the beginning of fields list (it's not
        included in `rest_framework.serializers.HyperlinkedModelSerializer`
        by default).
        """
        return (
            [model_info.pk.name] +
            super().get_default_field_names(declared_fields, model_info)
        )

    def get_fields(self, *args, **kwargs):
        """
        Bind every returned field to self (as a parent)
        """
        fields = super().get_fields(*args, **kwargs)
        # assign parent to every field as self
        for field_name, field in fields.items():
            if not field.parent:
                field.parent = self
        return fields

    def build_field(self, field_name, info, model_class, nested_depth):
        """
        Attach context with request to every nested field which is another
        serializer.
        """
        field_class, field_kwargs = super().build_field(
            field_name, info, model_class, nested_depth
        )
        if issubclass(field_class, serializers.BaseSerializer):
            field_kwargs.setdefault('context', {})['request'] = (
                self.context.get('request')
            )
        return field_class, field_kwargs

    def build_nested_field(self, field_name, relation_info, nested_depth):
        """
        Nested serializer is inheriting from `RalphAPISerializer`.
        """
        class NestedSerializer(RalphAPISerializer):
            class Meta:
                model = relation_info.related_model
                depth = nested_depth - 1
        field_class, field_kwargs = super().build_nested_field(
            field_name, relation_info, nested_depth
        )
        field_class = NestedSerializer
        return field_class, field_kwargs


class RalphAPISaveSerializer(
    TaggitSerializer,
    serializers.ModelSerializer,
    metaclass=DeclaredFieldsMetaclass
):
    serializer_choice_field = ReversedChoiceField
    serializer_related_field = relations.PrimaryKeyRelatedField

    def build_field(self, *args, **kwargs):
        field_class, field_kwargs = super().build_field(*args, **kwargs)
        # replace choice field by basic input
        # this affect browsable api form, which perform poorly when there is
        # lot of related objects (select_related couldn't be specified for them
        # so this sometimes results in n+1 SQL queries)
        # TODO: autocomplete field
        # http://www.django-rest-framework.org/topics/browsable-api/#customizing
        if issubclass(field_class, relations.RelatedField):
            field_kwargs.setdefault('style', {})['base_template'] = 'input.html'
        return field_class, field_kwargs


serializers_registry = {}


class RalphAPISerializerMetaclass(DeclaredFieldsMetaclass):
    def __new__(cls, name, bases, attrs):
        attrs['_serializers_registry'] = serializers_registry
        new_cls = super().__new__(cls, name, bases, attrs)
        meta = getattr(new_cls, 'Meta', None)
        if getattr(meta, 'model', None):
            serializers_registry[meta.model] = new_cls
        return new_cls


class RalphAPISerializer(
    RalphAPISerializerMixin,
    serializers.HyperlinkedModelSerializer,
    metaclass=RalphAPISerializerMetaclass
):
    pass
