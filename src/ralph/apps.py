# -*- coding: utf-8 -*-
from importlib import import_module

from django.apps import AppConfig


class RalphAppConfig(AppConfig):
    _load_modules_when_ready = ['urls', 'views']

    def ready(self):
        """
        Load modules specified in `_load_modules_when_ready` (urls and views)
        by default when app is ready.
        """
        super().ready()
        package = self.module.__name__
        for module in self._load_modules_when_ready:
            try:
                import_module('{}.{}'.format(package, module))
            except ImportError:
                pass
