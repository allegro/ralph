# Custom fields

## How to attach custom fields to your model?

Mix `WithCustomFieldsMixin` class to your model definition (import it from `ralph.lib.custom_fields.models`)

## Admin integration

To use custom fields in Django Admin for your model, mix `CustomFieldValueAdminMaxin` class to your model admin (import it from `ralph.lib.custom_fields.admin`)

## Django Rest Framework integration

To use custom fields in Django Rest Framework, mix `WithCustomFieldsSerializerMixin` class to your API serializer (import it from `ralph.lib.custom_fields.api`)

