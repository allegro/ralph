from django import forms
from django.contrib.contenttypes.forms import BaseGenericInlineFormSet
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext


class CustomFieldValueForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._replace_value_field()

    def _replace_value_field(self):
        # replace custom field value field with proper one (ex. select)
        if self.instance and self.instance.custom_field_id:
            self.fields['value'] = self.instance.custom_field.get_form_field()


class CustomFieldValueFormSet(BaseGenericInlineFormSet):
    def _construct_form(self, i, **kwargs):
        form = super()._construct_form(i, **kwargs)
        # fix for https://code.djangoproject.com/ticket/12028, together with
        # model's `_get_unique_checks`, which removes 'content_type' and
        # 'object_id' fields from excluded list for unique validation
        # instead of assigning content_type and object_id in save_new, like
        # BaseGenericInlineFormSet do, we're assigning it to form instance right
        # after form creation, to perform Django built-in unique validation
        setattr(
            form.instance,
            self.ct_field.get_attname(),
            ContentType.objects.get_for_model(self.instance).pk
        )
        setattr(
            form.instance,
            self.ct_fk_field.get_attname(),
            self.instance.pk
        )
        return form

    def get_unique_error_message(self, unique_check):
        return ugettext(
            'Please correct the duplicate data for custom fields (only one '
            'value for particular custom field is possible).'
        )
