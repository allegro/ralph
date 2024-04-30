# -*- coding: utf-8 -*-
from django.apps import AppConfig
from django.db.models.signals import post_migrate


class PermissionAppConfig(AppConfig):
    name = 'ralph.lib.permissions'
    verbose_name = 'Permissions'

    def ready(self):
        from ralph.lib.permissions.models import create_permissions
        from ralph.lib.permissions.views import update_extra_view_permissions
        post_migrate.disconnect(
            dispatch_uid='django.contrib.auth.management.create_permissions'
        )
        post_migrate.connect(create_permissions)
        post_migrate.connect(update_extra_view_permissions)
