from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from ralph.api.serializers import RalphAPISaveSerializer, RalphAPISerializer

from ..models import CustomField, CustomFieldValue
from .fields import CustomFieldValueHyperlinkedIdentityField


class CustomFieldSimpleSerializer(RalphAPISerializer):
    class Meta:
        model = CustomField
        fields = ('name', 'attribute_name', 'type', 'default_value')


class CustomFieldValueSerializerMixin(object):
    """
    Mixin with utilities for CustomFieldValue serializers

    * handles related_model arg
    * handles url field to nested custom field value resource
    """
    # default field class to use for url field
    custom_field_value_url_field = CustomFieldValueHyperlinkedIdentityField
    # nested resource name used by `NestedCustomFieldsRouterMixin`
    custom_fields_nested_resource_base_name = 'customfields'

    class Meta:
        model = CustomFieldValue
        fields = ('id', 'url', 'custom_field', 'value')

    def __init__(self, *args, **kwargs):
        self.related_model = kwargs.pop('related_model')
        super().__init__(*args, **kwargs)

    def build_url_field(self, field_name, model_class):
        """
        Create a field representing the object's own URL.
        """
        if field_name == 'url':
            # use dedicated serializer for url field to get "nested" url
            # for custom field value (in context of other object)
            field_class = self.custom_field_value_url_field
            field_kwargs = self._get_custom_field_value_url_kwargs(model_class)
        else:
            field_class, field_kwargs = super().build_url_field(
                field_name, model_class
            )
        return field_class, field_kwargs

    def _get_custom_field_value_url_kwargs(self, model_class):
        return {
            'view_name': '{}-{}-detail'.format(
                self.related_model._meta.model_name,
                self.custom_fields_nested_resource_base_name
            ),
        }


from django.core import exceptions
from rest_framework.exceptions import ValidationError
class Xxx(serializers.PrimaryKeyRelatedField):
    alt_lookup_field = None

    def __init__(self, **kwargs):
        self.alt_lookup_field = kwargs.pop('alt_lookup_field', None)
        assert self.alt_lookup_field != None, "alt_lookup_field is required"
        super().__init__(**kwargs)

    def to_internal_value(self, data):
        filters = {
            self.alt_lookup_field: data
        }
        try:
            print('data', data)
            data = self.get_queryset().get(**filters).id
        except exceptions.MultipleObjectsReturned as e:
            msg = 'Multiple objects found for {}={}'.format(
                self.alt_lookup_field, data
            )
            raise ValidationError(msg)
        except exceptions.ObjectDoesNotExist as e:
            msg = 'Can\'t find object with {}={}'.format(
                self.alt_lookup_field, data
            )
            raise ValidationError(msg)
        return super().to_internal_value(data)


class CustomFieldValueSaveSerializer(
    CustomFieldValueSerializerMixin, RalphAPISaveSerializer
):
    custom_field = Xxx(
        queryset=CustomField.objects.all(), alt_lookup_field='attribute_name',
    )

    def to_internal_value(self, data):
        result = super().to_internal_value(data)
        # rewrite content type id and object id (grabbed from url) to validated
        # data
        for key in ['content_type_id', 'object_id']:
            if key in data:
                result[key] = data[key]
        return result

    def _extra_instance_validation(self, instance):
        super()._extra_instance_validation(instance)
        # run extra uniqueness validation - since content_type and object_id
        # fields are not exposed through API (we're using nested resources),
        # DRF does not handle this validation automatically
        try:
            instance.validate_unique()
        except DjangoValidationError as e:
            raise self._django_validation_error_to_drf_validation_error(e)


class CustomFieldValueSerializer(
    CustomFieldValueSerializerMixin, RalphAPISerializer
):
    custom_field = CustomFieldSimpleSerializer()

    class Meta:
        model = CustomFieldValue
        fields = ('id', 'custom_field', 'value', 'url')


class WithCustomFieldsSerializerMixin(serializers.Serializer):
    """
    Mixin for other serializers which should have custom fields attached.

    Presents custom fields for single object as a dictionary, where key is
    attribute_name of custom_field and value is value of custom field.
    """
    custom_fields = serializers.SerializerMethodField()
    configuration_variables = serializers.SerializerMethodField()

    def get_custom_fields(self, obj):
        # use base manager to not execute separated query when
        # custom fields are included in prefetch_related
        return {
            cfv.custom_field.attribute_name: cfv.value
            for cfv in obj.custom_fields.all()
        }

    def get_configuration_variables(self, obj):
        # use base manager to not execute separated query when
        # custom fields are included in prefetch_related
        return {
            cfv.custom_field.attribute_name: cfv.value
            for cfv in obj.custom_fields.all()
            if cfv.custom_field.use_as_configuration_variable
        }
