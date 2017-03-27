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
        from ralph.operations.changemanagement.subscribtions import receive_chm_event  # noqa
