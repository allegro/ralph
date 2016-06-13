import six
from django.utils.translation import ugettext_lazy as _
from rest_framework.serializers import CharField, ChoiceField

from .forms import OTHER


class ChoiceFieldWithOtherOptionField(ChoiceField):
    """
    Serializer for choice field with other option. This field accepts single,
    plain value as regular ChoiceField or compound value - dict - where `value`
    is choice value and (optionally) `__other__` to specify other value.
    """
    other_option_label = _('Other')
    other_field = CharField()

    def __init__(
        self, choices, other_option_label=None, other_field=None,
        auto_other_choice=True, *args, **kwargs
    ):
        self.auto_other_choice = auto_other_choice
        self.other_option_label = other_option_label or self.other_option_label
        self.other_field = other_field or self.other_field
        choices = list(choices)
        if self.auto_other_choice:
            choices += [(OTHER, self.other_option_label)]
        super().__init__(choices=choices, *args, **kwargs)

    def to_internal_value(self, data):
        if not isinstance(data, dict):
            data = {'value': data}
        value = {
            'value': super().to_internal_value(data.get('value'))
        }
        if value['value'] == OTHER:
            value[OTHER] = self._validate_other(data[OTHER])
        return value

    def _validate_other(self, data):
        return self.other_field.run_validation(data)

    def to_representation(self, value):
        return six.text_type(value)
