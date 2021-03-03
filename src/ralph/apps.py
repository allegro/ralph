# -*- coding: utf-8 -*-
from importlib import import_module

from django.apps import AppConfig
from django.core import serializers


class RalphAppConfig(AppConfig):
    def get_load_modules_when_ready(self):
        return ['subscribers', 'views']

    def ready(self):
        """
        Load modules returned by `get_load_modules_when_ready` by default
        when app is ready.
        """
        super().ready()

        serializers.register_serializer("json", "ralph.lib.serializers")

        package = self.module.__name__
        for module in self.get_load_modules_when_ready():
            try:
                import_module('{}.{}'.format(package, module))
            except ImportError:
                pass
