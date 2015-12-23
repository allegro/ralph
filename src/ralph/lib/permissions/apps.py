# -*- coding: utf-8 -*-
from django.apps import AppConfig
from django.db.models.signals import post_migrate


class PermissionAppConfig(AppConfig):
    name = 'ralph.lib.permissions'
    verbose_name = 'Permissions'

    def ready(self):
        from ralph.lib.permissions.views import update_extra_view_permissions
        post_migrate.connect(update_extra_view_permissions)
