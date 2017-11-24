# -*- coding: utf-8 -*-
from django.apps import AppConfig
from django.conf import settings
from django.core.checks import register

from ralph.lib.transitions.checks import check_transition_templates


class TransitionAppConfig(AppConfig):
    name = 'ralph.lib.transitions'
    verbose_name = 'Transitions'


@register()
def check_transition_settings(app_configs, **kwargs):
    errors = []
    transition_templates = getattr(settings, 'TRANSITION_TEMPLATES', None)
    errors.extend(check_transition_templates(transition_templates))
    return errors
