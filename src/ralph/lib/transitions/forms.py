# -*- coding: utf-8 -*-
from django import forms
from django.conf import settings
from django.utils.html import strip_tags
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from ralph.lib.transitions.models import (
    Action,
    Transition,
    TRANSITION_ORIGINAL_STATUS,
    TransitionModel
)

TRANSITION_TEMPLATES = settings.TRANSITION_TEMPLATES


def wrap_action_name(action):
    """
    Add additional information to action name (infotip, async icon).
    """
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
    if action.is_async:
        verbose_name = verbose_name + """
        &nbsp;<i
        data-tooltip
        class="has-tip async fa fa-hourglass-half"
        title='Asynchronous'></i>
        """
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
        async_services = list(settings.RALPH_INTERNAL_SERVICES.keys())
        self.fields['async_service_name'] = forms.ChoiceField(
            choices=(
                (('', '-------'),) + tuple(zip(async_services, async_services))
            ),
            required=False,
        )
        actions_choices = [
            (i.id, wrap_action_name(getattr(self.model, i.name)))
            for i in Action.objects.filter(
                content_type=self._transition_model_instance.content_type
            )
        ]
        self.fields['actions'].widget = forms.CheckboxSelectMultiple(
            choices=actions_choices
        )
        self.fields['actions'].required = False
        self.fields['template_name'] = forms.ChoiceField(
            choices=(('', _('Default')),),
            required=False
        )
        if TRANSITION_TEMPLATES:
            self.fields['template_name'].choices += tuple(TRANSITION_TEMPLATES)
        else:
            self.fields['template_name'].widget.attrs['disabled'] = True

    def clean(self):
        self.cleaned_data['actions'] = [a.id for a in self.cleaned_data['actions']]
        cleaned_data = super().clean()
        actions = Action.objects.in_bulk(cleaned_data['actions'])
        attachment_counter = 0
        one_action = False
        one_action_name = ''
        any_async_action = False
        actions_items = actions.items()
        for k, v in actions_items:
            action = getattr(self.model, v.name)
            if getattr(action, 'return_attachment', False):
                attachment_counter += 1
            if getattr(action, 'only_one_action', False):
                one_action = True
                one_action_name = getattr(action, 'verbose_name', '')
            any_async_action |= action.is_async

        if one_action and len(actions_items) > 1:
            msg = _(
                (
                    'You have chosen action: %(name)s can only be selected'
                    ' for transition'
                )
            ) % {'name': one_action_name}
            self.add_error('actions', msg)
        # check async options
        if any_async_action and not cleaned_data['run_asynchronously']:
            cleaned_data['run_asynchronously'] = True
        if (
            cleaned_data['run_asynchronously'] and
            not cleaned_data.get('async_service_name')
        ):
            msg = _(
                'Please provide async service name for asynchronous transition'
            )
            if any_async_action:
                msg = '{}{}'.format(
                    msg, _(' (At least one of chosen actions is asynchronous)')
                )
            self.add_error('async_service_name', msg)

        return cleaned_data

    class Meta:
        model = Transition
        fields = [
            'name', 'source', 'target', 'run_asynchronously',
            'async_service_name', 'template_name', 'success_url', 'actions',
        ]
