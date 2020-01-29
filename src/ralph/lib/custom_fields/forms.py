from django import forms
from django.contrib.contenttypes.forms import BaseGenericInlineFormSet
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext


class CustomFieldValueForm(forms.ModelForm):
    class Meta:
        fields = ['custom_field', 'value']

    def __init__(self, request=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request
        self._replace_value_field()

    def _replace_value_field(self):
        # replace custom field value field with proper one (ex. select)
        if self.instance and self.instance.custom_field_id:
            self.fields['value'] = self.instance.custom_field.get_form_field()

    def clean(self):
        clean_data = super().clean()
        custom_field = clean_data.get('custom_field')

        if custom_field:
            if (
                custom_field.managing_group is not None and
                custom_field.managing_group not in self.request.user.groups.all()  # noqa: E501
            ):
                self.add_error(
                    'custom_field',
                    ValidationError(
                        _(
                            'Only users from {} group can set '
                            'this custom field.'
                        ).format(custom_field.managing_group.name),
                        code='invalid'
                    )
                )

        return clean_data


class CustomFieldValueWithClearChildrenForm(CustomFieldValueForm):
    clear_children = forms.BooleanField(
        initial=False, required=False, label=_('Clear children values?'),
    )

    class Meta(CustomFieldValueForm.Meta):
        fields = CustomFieldValueForm.Meta.fields + ['clear_children']

    def save(self, *args, **kwargs):
        result = super().save(*args, **kwargs)
        # clear custom fields values for particular custom field if
        # clear_children is checked
        if self.cleaned_data['clear_children']:
            self.instance.object.clear_children_custom_field_value(
                self.instance.custom_field,
            )
        return result


class CustomFieldValueFormSet(BaseGenericInlineFormSet):

    def __init__(self, request=None, queryset=None, *args, **kwargs):
        self.request = request

        # (sjasinski) Custom fields requiring permissions will be displayed
        # in places where we have access to information about logged in user
        # (which we extract from request). If we don't have this
        # information (for example, in VersionAdmin), such fields
        # will not be displayed at all. They will have to be edited manually
        # in standard RalphAdmin form. This is because in some places
        # there is no easy way to inject request object to FormSets without
        # some horrible hacking or manual rewrite of some very long methods.
        query_filter = Q(custom_field__managing_group__isnull=True)
        if getattr(self.request, 'user', None):
            query_filter = query_filter | Q(
                custom_field__managing_group__in=self.request.user.groups.all()
            )
        queryset = queryset.filter(query_filter)

        super().__init__(queryset=queryset, *args, **kwargs)

    def _construct_form(self, i, **kwargs):
        form = super()._construct_form(i, request=self.request, **kwargs)
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
