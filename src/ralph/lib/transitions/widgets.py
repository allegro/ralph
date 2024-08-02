from django.forms.widgets import (
    CheckboxFieldRenderer,
    CheckboxSelectMultiple,
    ChoiceInput
)


class _CheckboxQuerySetChoiceInput(ChoiceInput):
    input_type = 'checkbox'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.value = set(str(v.id) for v in self.value)

    def is_checked(self):
        return self.choice_value in self.value


class _QuerySetCheckboxRenderer(CheckboxFieldRenderer):
    choice_input_class = _CheckboxQuerySetChoiceInput


class ActionSelectWidget(CheckboxSelectMultiple):
    renderer = _QuerySetCheckboxRenderer
