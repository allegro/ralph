# -*- coding: utf-8 -*-

from ralph.apps import RalphAppConfig


class SecurityConfig(RalphAppConfig):
    name = "ralph.security"
    verbose_name = "Security"
    default = True
