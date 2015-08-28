# -*- coding: utf-8 -*-
import io
from os.path import abspath, dirname, join

from django.apps import apps
from django.template import TemplateDoesNotExist
from django.template.loaders.base import Loader as BaseLoader


class AppTemplateLoader(BaseLoader):
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

    def get_template_path(self, template_name, template_dirs=None):
        """
        Try to split template name by ':' to get app_label
        """
        template_parts = template_name.split(":", 1)

        if len(template_parts) != 2:
            raise TemplateDoesNotExist()

        app_label, template_name = template_parts
        app = apps.get_app_config(app_label)
        app_dir = dirname(app.module.__file__)
        template_dir = abspath(join(app_dir, 'templates'))
        return join(template_dir, template_name)

    def load_template_source(self, template_name, template_dirs=None):
        filepath = self.get_template_path(template_name, template_dirs)
        try:
            with io.open(filepath, encoding=self.engine.file_charset) as fp:
                return fp.read(), filepath
        except IOError:
            raise TemplateDoesNotExist(template_name)
