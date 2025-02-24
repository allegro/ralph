# -*- coding: utf-8 -*-
from ralph.apps import RalphAppConfig


class DCViewConfig(RalphAppConfig):
    name = "ralph.dc_view"
    verbose_name = "DC View"

    def ready(self):
        super().ready()
        from ralph.dc_view.views.ui import ServerRoomView  # Noqa
