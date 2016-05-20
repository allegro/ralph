# -*- coding: utf-8 -*-
from django import forms
from django.utils.translation import ugettext_lazy as _


class RequestFormMixin(object):
    """
    Form which has access to request and user
    """
    def __init__(self, *args, **kwargs):
        if not hasattr(self, '_request') or not self._request:
            self._request = kwargs.pop('_request', None)
        if not hasattr(self, '_user'):
            self._user = kwargs.pop(
                '_user',
                self._request.user if self._request else None
            )
        super().__init__(*args, **kwargs)


class RequestModelForm(RequestFormMixin, forms.ModelForm):
    pass


OTHER = '__other__'
OTHER_NAME = '{}' + OTHER


class SelectWithOtherOpitonWidget(forms.Select):
    css_class = 'select-other'

    class Media:
        js = ('src/js/widgets.js',)

    def _get_other_field(self, name, value):
        return forms.TextInput().render(
            name=OTHER_NAME.format(name), value=value.get(OTHER) or ''
        )

    def render(self, name, value, attrs=None, choices=()):
        show_other = value and value.get('value') == OTHER
        choice_value = (value.get('value') if value else '') or ''
        return '<div class="{}">{}{}</div>'.format(
            self.css_class,
            super().render(name, choice_value, attrs=attrs, choices=choices),
            self._get_other_field(name, value) if show_other else ''
        )

    def value_from_datadict(self, data, files, name):
        return {
            'value': data.get(name, None),
            OTHER: data.get(OTHER_NAME.format(name), None)
        }


class ChoiceFieldWithOtherOption(forms.ChoiceField):
    widget = SelectWithOtherOpitonWidget
    other_option_label = _('Other')
    other_field = forms.CharField()

    def __init__(
        self, other_option_label=None, other_field=None, *args, **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.other_option_label = other_option_label or self.other_option_label
        self.other_field = other_field or self.other_field

    def _get_choices(self):
        return super()._get_choices()

    def _set_choices(self, value):
        value = list(value) + [(OTHER, self.other_option_label)]
        self._choices = self.widget.choices = value

    choices = property(_get_choices, _set_choices)

    def _validate_other(self, value):
        return self.other_field.clean(value)

    def clean(self, value):
        value['value'] = super().clean(value['value'])
        if value['value'] == OTHER:
            value[OTHER] = self._validate_other(value[OTHER])
        return value

    def to_python(self, value):
        return value
