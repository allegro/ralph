# -*- coding: utf-8 -*-
from django.apps import AppConfig

from ralph.lib.transitions.models import update_models_attrs


class TransitionAppConfig(AppConfig):
    name = 'ralph.lib.transitions'
    verbose_name = 'Transitions'

    def ready(self):
        try:
            # RuntimeError raised when database is empty (e.g. after tests).
            # The best solution would be run update_models_attrs after loaded
            # all apps. Django apps mechanism doesn't have any signal for
            # this sitiuation.
            update_models_attrs()
        except RuntimeError:
            pass
