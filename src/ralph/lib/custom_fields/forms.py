from django import forms
from django.contrib.contenttypes.forms import BaseGenericInlineFormSet
from django.contrib.contenttypes.models import ContentType
from django.forms.forms import BoundField
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext


class DisablableBoundField(BoundField):
    def as_widget(self, widget=None, attrs=None, only_initial=False):
        """
        Renders the field by rendering the passed widget, adding any HTML
        attributes passed as attrs.  If no widget is specified, then the
        field's default widget will be used.
        """
        if not widget:
            widget = self.field.widget

        if self.field.localize:
            widget.is_localized = True

        attrs = attrs or {}
        import pdb; pdb.set_trace()
        if self.field.disabled:
            attrs['disabled'] = True
        auto_id = self.auto_id
        if auto_id and 'id' not in attrs and 'id' not in widget.attrs:
            if not only_initial:
                attrs['id'] = auto_id
            else:
                attrs['id'] = self.html_initial_id

        if not only_initial:
            name = self.html_name
        else:
            name = self.html_initial_name
        return force_text(widget.render(name, self.value(), attrs=attrs))

class CustomFieldValueForm(forms.ModelForm):
    class Meta:
        fields = ['custom_field', 'value']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._replace_value_field()

    def _replace_value_field(self):
        # replace custom field value field with proper one (ex. select)
        if self.instance and self.instance.custom_field_id:
            self.fields['value'] = self.instance.custom_field.get_form_field(disabled=True)

    def _clean_fields(self):
        for name, field in self.fields.items():
            if field.disabled:
                value = self.initial.get(name, field.initial)

        super()._clean_fields()

    def __getitem__(self, name):
        "Returns a BoundField with the given name."
        try:
            import pdb; pdb.set_trace()
            field = self.fields[name]
        except KeyError:
            raise KeyError(
                "Key %r not found in '%s'" % (
                name, self.__class__.__name__))
        if name not in self._bound_fields_cache:
            self._bound_fields_cache[name] = DisablableBoundField(self, field, name)
        return self._bound_fields_cache[name]


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
