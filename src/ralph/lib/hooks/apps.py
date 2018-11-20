# -*- coding: utf-8 -*-
from django.apps import AppConfig
from django.core.checks import register

from ralph.lib.hooks.checks import check_configuration


class HooksAppConfig(AppConfig):
    name = 'ralph.lib.hooks'
    verbose_name = 'Hooks'


register(check_configuration)
