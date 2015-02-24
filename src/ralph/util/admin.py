from django.contrib import admin

from ralph.util.models import (
    CustomAttribute,
    CustomAttributeIntegerValue,
    CustomAttributeOption,
    CustomAttributeSingleChoiceValue,
    CustomAttributeStringValue,
)

for Model in [
    CustomAttribute,
    CustomAttributeIntegerValue,
    CustomAttributeOption,
    CustomAttributeSingleChoiceValue,
    CustomAttributeStringValue,
]:
    admin.site.register(Model)
