# -*- coding: utf-8 -*-
from django.apps import AppConfig


class ReportsConfig(AppConfig):
    name = 'ralph.reports'
    verbose_name = 'Reports'

    def ready(self):
        from ralph.reports import views  # noqa
