# -*- coding: utf-8 -*-
from django.apps import AppConfig

from ralph.admin.filters import register_custom_filters


class RalphAdminConfig(AppConfig):
    name = 'ralph.admin'
    label = 'ralph_admin'
    verbose_name = 'Ralph Admin'

    def ready(self):
        register_custom_filters()
