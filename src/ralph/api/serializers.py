# -*- coding: utf-8 -*-
import logging
import operator
from functools import reduce

from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.exceptions import NON_FIELD_ERRORS, ObjectDoesNotExist
from django.db import transaction
from django.db.models import Q
from django.db.models.fields import exceptions
from rest_framework import permissions, relations, serializers
from rest_framework.exceptions import \
    ValidationError as RestFrameworkValidationError
from rest_framework.settings import api_settings
from rest_framework.utils import model_meta
from reversion import revisions as reversion
from taggit_serializer.serializers import (
    TaggitSerializer,
    TagListSerializerField
)

from ralph.api.fields import AbsoluteUrlField, ReversedChoiceField
from ralph.api.relations import RalphHyperlinkedRelatedField, RalphRelatedField
from ralph.lib.mixins.models import AdminAbsoluteUrlMixin, TaggableMixin
from ralph.lib.permissions.api import (
    PermissionsPerFieldSerializerMixin,
    RelatedObjectsPermissionsSerializerMixin
)

logger = logging.getLogger(__name__)

NESTED_SERIALIZER_FIELDS_BLACKLIST = ["content_type", "password"]


class AdditionalLookupRelatedField(serializers.PrimaryKeyRelatedField):
    """
    Allows to lookup related field (foreign key) by fields other than pk.
    """

    def __init__(self, lookup_fields, *args, **kwargs):
        self.lookup_fields = lookup_fields
        super().__init__(*args, **kwargs)

    def to_internal_value(self, data):
        query = [Q(**{f: data}) for f in self.lookup_fields]
        try:
            pk = int(data)
        except ValueError:
            pass
        else:
            query.append(Q(pk=pk))
        try:
            return self.get_queryset().get(reduce(operator.or_, query))
        except ObjectDoesNotExist:
            self.fail("does_not_exist", pk_value=data)
        except (TypeError, ValueError):
            self.fail("incorrect_type", data_type=type(data).__name__)


class DeclaredFieldsMetaclass(serializers.SerializerMetaclass):
    """
    Add additional declared fields in specific cases.

    When serializer's model inherits from
    `ralph.lib.mixins.models.TaggableMixin`, tags field is attached.
    """

    def __new__(cls, name, bases, attrs):
        meta = attrs.get("Meta")
        model = getattr(meta, "model", None)
        fields = getattr(meta, "fields", None)
        if (
            model
            and issubclass(model, TaggableMixin)
            and not getattr(attrs.get("Meta"), "_skip_tags_field", False)
        ):
            attrs["tags"] = TagListSerializerField(required=False)
            attrs["prefetch_related"] = list(attrs.get("prefetch_related", [])) + [
                "tags"
            ]

        if model and issubclass(model, AdminAbsoluteUrlMixin):
            attrs["ui_url"] = AbsoluteUrlField()
            if fields and isinstance(fields, (list, tuple)):
                meta.fields += ("ui_url",)
        return super().__new__(cls, name, bases, attrs)


class RalphAPISerializerMixin(
    TaggitSerializer,
    RelatedObjectsPermissionsSerializerMixin,
    PermissionsPerFieldSerializerMixin,
    metaclass=DeclaredFieldsMetaclass,  # noqa
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

    # This switch disable `url` fields in serializers
    # Ralph uses serializers mainly with http requests, but occasionally we
    # need to use Ralph serializers with django signals (if so there is no
    # request, and all `url` fields in serializers are irrelevant)
    skip_url_when_no_request = True
    serializer_choice_field = ReversedChoiceField

    @property
    def serializer_related_field(self):
        """
        When it's safe request (ex. GET), related serailizer is hyperlinked
        (contains url to related object). When it's not safe request (ex. POST),
        serializer expect to pass only PK for related object.
        """
        if (
            self.context.get("request")
            and self.context["request"].method in permissions.SAFE_METHODS
        ):  # noqa
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
        return [model_info.pk.name] + super().get_default_field_names(
            declared_fields, model_info
        )

    def get_fields(self, *args, **kwargs):
        """
        Bind every returned field to self (as a parent)
        """
        fields = super().get_fields(*args, **kwargs)
        if (
            self.skip_url_when_no_request
            and not self.context.get("request")
            and api_settings.URL_FIELD_NAME in fields
        ):
            del fields[api_settings.URL_FIELD_NAME]

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
            field_kwargs.setdefault("context", {})["request"] = self.context.get(
                "request"
            )
        return field_class, field_kwargs

    def build_nested_field(self, field_name, relation_info, nested_depth):
        """
        Nested serializer is inheriting from `RalphAPISerializer`.
        """

        class NestedMeta:
            model = relation_info.related_model
            depth = nested_depth - 1
            # don't register this serializer as main model serializer
            exclude_from_registry = True
            exclude = []

        # exclude some fields from nested serializer
        for field in NESTED_SERIALIZER_FIELDS_BLACKLIST:
            try:
                relation_info.related_model._meta.get_field(field)
            except exceptions.FieldDoesNotExist:
                pass
            else:
                NestedMeta.exclude.append(field)

        class NestedSerializer(RalphAPISerializer):
            Meta = NestedMeta

        field_class, field_kwargs = super().build_nested_field(
            field_name, relation_info, nested_depth
        )
        field_class = NestedSerializer
        return field_class, field_kwargs


class ReversionHistoryAPISerializerMixin(serializers.ModelSerializer):
    @property
    def _save_history(self) -> bool:
        try:
            return self.Meta.save_history
        except AttributeError:
            return True

    def save(self):
        if self._save_history:
            with transaction.atomic(), reversion.create_revision():
                reversion.set_comment("API Save")
                reversion.set_user(self.context["request"].user)
                return super().save()
        else:
            return super().save()


class RalphAPISaveSerializer(
    TaggitSerializer,
    ReversionHistoryAPISerializerMixin,
    metaclass=DeclaredFieldsMetaclass,
):
    serializer_choice_field = ReversedChoiceField
    serializer_related_field = relations.PrimaryKeyRelatedField

    # set this to False if you don't want to run model's clean method validation
    # this could be useful if you have custom `create` method in serializer
    _validate_using_model_clean = True

    def build_field(self, *args, **kwargs):
        field_class, field_kwargs = super().build_field(*args, **kwargs)
        # replace choice field by basic input
        # this affect browsable api form, which perform poorly when there is
        # lot of related objects (select_related couldn't be specified for them
        # so this sometimes results in n+1 SQL queries)
        # TODO: autocomplete field
        # http://www.django-rest-framework.org/topics/browsable-api/#customizing
        if issubclass(field_class, relations.RelatedField):
            field_kwargs.setdefault("style", {})["base_template"] = "input.html"
        return field_class, field_kwargs

    def _validate_model_clean(self, attrs):
        """
        Run validation using model's clean method.
        """
        data = attrs.copy()
        ModelClass = self.Meta.model
        # Remove many-to-many relationships from validated_data.
        # They are not valid arguments to the model initializer.
        info = model_meta.get_field_info(ModelClass)
        for field_name, relation_info in info.relations.items():
            if relation_info.to_many and (field_name in data):
                data.pop(field_name)

        # remove tags field
        self._pop_tags(data)

        # self.instance is set in case of update (PATCH/PUT) call
        # otherwise create new model instance
        instance = self.instance or ModelClass()
        for k, v in data.items():
            setattr(instance, k, v)
        try:
            instance.clean()
        except DjangoValidationError as e:
            raise self._django_validation_error_to_drf_validation_error(e)
        self._extra_instance_validation(instance)

    def _django_validation_error_to_drf_validation_error(self, exc):
        # convert Django ValidationError to rest framework
        # ValidationError to display errors per field
        # (the standard behaviour of DRF is to dump all Django
        # ValidationErrors into "non_field_errors" result field)
        if hasattr(exc, "error_dict"):
            return RestFrameworkValidationError(detail=dict(list(exc)))
        else:
            return RestFrameworkValidationError(
                detail=dict([(NON_FIELD_ERRORS, [value]) for value in exc])
            )

    def _extra_instance_validation(self, instance):
        pass

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if self._validate_using_model_clean:
            self._validate_model_clean(attrs)
        return attrs


serializers_registry = {}


class RalphAPISerializerMetaclass(DeclaredFieldsMetaclass):
    def __new__(cls, name, bases, attrs):
        attrs["_serializers_registry"] = serializers_registry
        new_cls = super().__new__(cls, name, bases, attrs)
        meta = getattr(new_cls, "Meta", None)
        if getattr(meta, "model", None) and not getattr(
            meta, "exclude_from_registry", False
        ):
            serializers_registry[meta.model] = new_cls
        return new_cls


class RalphAPISerializer(
    RalphAPISerializerMixin,
    serializers.HyperlinkedModelSerializer,
    metaclass=RalphAPISerializerMetaclass,
):
    pass
