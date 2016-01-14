# -*- coding: utf-8 -*-
from django import forms
from django.utils.html import strip_tags
from django.utils.text import mark_safe
from django.utils.translation import ugettext_lazy as _

from ralph.lib.transitions.models import (
    Action,
    Transition,
    TRANSITION_ORIGINAL_STATUS,
    TransitionModel
)


def wrap_action_name(action):
    verbose_name = action.verbose_name
    help_text = action.help_text
    if help_text:
        verbose_name = verbose_name + """
        &nbsp;<i
            data-tooltip
            class="has-tip fa fa-info-circle"
            title='{txt}'></i>
        """.format(
            txt=strip_tags(str(help_text)),
        )
    return mark_safe(verbose_name)


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
            choices=(('', '-------'),) + choices + (
                TRANSITION_ORIGINAL_STATUS,
            )
        )
        actions_choices = [
            (i.id, wrap_action_name(getattr(self.model, i.name)))
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
        one_action = False
        one_action_name = ''
        actions_items = actions.items()
        for k, v in actions_items:
            action = getattr(self.model, v.name)
            if getattr(action, 'return_attachment', False):
                attachment_counter += 1
            if getattr(action, 'only_one_action', False):
                one_action = True
                one_action_name = getattr(action, 'verbose_name', '')

        if attachment_counter > 1:
            msg = _(
                'Please select at most one action which return attachment.'
            )
            self.add_error('actions', msg)
        if one_action and len(actions_items) > 1:
            msg = _(
                (
                    'You have chosen action: %(name)s can only be selected'
                    ' for transition'
                )
            ) % {'name': one_action_name}
            self.add_error('actions', msg)
        return cleaned_data

    class Meta:
        model = Transition
        fields = ['name', 'source', 'target', 'actions']
