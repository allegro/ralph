# -*- coding: utf-8 -*-

from ralph.apps import RalphAppConfig


class SecurityConfig(RalphAppConfig):
    name = "ralph.security"
    verbose_name = "Security"

    def get_load_modules_when_ready(self):
        """
        security/transitions.py will be loaded alongside modules returned by
        super().get_load_modules_when_ready() when the app is ready.
        This will add transition actions to appropriate models.
        """
        return super().get_load_modules_when_ready() + ["transitions"]
