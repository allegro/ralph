# -*- coding: utf-8 -*-
from django import forms
from django.utils.translation import ugettext_lazy as _

from ralph.lib.transitions.models import Action, Transition, TransitionModel


class TransitionForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        if not hasattr(self, '_transition_model_instance'):
            raise ValueError
        if not isinstance(self._transition_model_instance, TransitionModel):
            raise TypeError
        super().__init__(*args, **kwargs)
        self.model = self._transition_model_instance.content_type.model_class()
        field_name = self._transition_model_instance.field_name
        choices = tuple(self.model._meta.get_field(field_name).choices)
        self.fields['source'] = forms.MultipleChoiceField(choices=choices)
        self.fields['target'] = forms.ChoiceField(
            choices=(('', '-------'),) + choices
        )
        import ipdb; ipdb.set_trace()
        actions_choices = [
            (i.id, getattr(self.model, i.name).verbose_name)
            for i in Action.objects.filter(
                content_type=self._transition_model_instance.content_type
            )
        ]
        self.fields['actions'] = forms.MultipleChoiceField(
            choices=actions_choices, widget=forms.CheckboxSelectMultiple()
        )
        self.fields['actions'].required = False

    def clean(self):
        cleaned_data = super().clean()
        actions = Action.objects.in_bulk(cleaned_data['actions'])
        attachment_counter = 0
        for k, v in actions.items():
            action = getattr(self.model, v.name)
            if getattr(action, 'return_attachment', False):
                attachment_counter += 1
        if attachment_counter > 1:
            msg = _(
                'Please select at most one action which return attachment.'
            )
            self.add_error('actions', msg)
        return cleaned_data

    class Meta:
        model = Transition
        fields = ['name', 'source', 'target', 'actions']
