from factory import DjangoModelFactory
from factory.fuzzy import FuzzyText

from ralph.lib.custom_fields.models import (
    CustomField,
    CustomFieldTypes,
    CustomFieldValue
)


class CustomFieldFactory(DjangoModelFactory):
    name = FuzzyText(length=10)
    type = CustomFieldTypes.STRING
    default_value = FuzzyText(length=10)

    class Meta:
        model = CustomField
        django_get_or_create = ['name',]
