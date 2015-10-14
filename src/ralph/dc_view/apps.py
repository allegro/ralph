# -*- coding: utf-8 -*-
from django.apps import AppConfig


class DCViewConfig(AppConfig):
    name = 'ralph.dc_view'
    verbose_name = 'DC View'

    def ready(self):
        from ralph.dc_view.views.ui import DataCenterView  # Noqa
