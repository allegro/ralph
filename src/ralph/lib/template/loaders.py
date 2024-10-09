# -*- coding: utf-8 -*-
from os.path import abspath, dirname, join

from django.apps import apps
from django.template import Origin
from django.template.loader import TemplateDoesNotExist
from django.template.loaders.filesystem import Loader


class AppTemplateLoader(Loader):
    """
    Template loader which allow to specify application label from which
    template should be used (for example when extending).

    Usage: specify template path as ``<app_label>:<template_path>``

    App label should be specified in Django AppConfig. Check
    https://docs.djangoproject.com/en/1.8/ref/applications/ for more details

    Example ::

        {% extends "ralph_admin:admin/base.html" %}

    To use this loader add it in your settings ::

        TEMPLATES = [
            {
                ...
                'OPTIONS': {
                    ...
                    'loaders': [
                        'django.template.loaders.filesystem.Loader',
                        'django.template.loaders.app_directories.Loader',
                        'ralph.lib.template.loaders.AppTemplateLoader',
                    ],
                    ...
                },
                ...
            },
        ]

    Loader is based on this snippet: https://djangosnippets.org/snippets/1376/
    """
    is_usable = True

    def get_template_path(self, template_name):
        """
        Try to split template name by ':' to get app_label
        """
        template_parts = template_name.split(":", 1)

        if len(template_parts) != 2:
            raise TemplateDoesNotExist(template_name)

        app_label, template_name = template_parts
        app = apps.get_app_config(app_label)
        app_dir = dirname(app.module.__file__)
        template_dir = abspath(join(app_dir, 'templates'))
        return join(template_dir, template_name)

    def get_template_sources(self, template_name):
        filepath = self.get_template_path(template_name)
        yield Origin(name=filepath, template_name=template_name, loader=self)
