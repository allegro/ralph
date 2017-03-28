# -*- coding: utf-8 -*-
from ralph.admin.filters import register_custom_filters
from ralph.apps import RalphAppConfig


class RalphAdminConfig(RalphAppConfig):
    name = 'ralph.admin'
    label = 'ralph_admin'
    verbose_name = 'Ralph Admin'

    def ready(self):
        register_custom_filters()
        super().ready()
