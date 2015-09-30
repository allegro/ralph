# -*- coding: utf-8 -*-
from django.apps import AppConfig
from django.db.models.signals import post_migrate

from ralph.lib.permissions.views import update_extra_view_permissions


class PermissionAppConfig(AppConfig):
    name = 'ralph.lib.permissions'
    verbose_name = 'Permissions'

    def ready(self):
        post_migrate.connect(update_extra_view_permissions)
