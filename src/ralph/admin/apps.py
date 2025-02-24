# -*- coding: utf-8 -*-

from ralph.apps import RalphAppConfig


class RalphAdminConfig(RalphAppConfig):
    name = "ralph.admin"
    label = "ralph_admin"
    verbose_name = "Ralph Admin"

    def ready(self):
        from ralph.admin.filters import register_custom_filters

        register_custom_filters()
        super().ready()
