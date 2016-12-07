# -*- coding: utf-8 -*-
from django.conf import settings
from django.db.models.signals import post_save
from ralph.apps import RalphAppConfig
from ralph.notifications.sender import send_notification_for_model


class NotificationConfig(RalphAppConfig):
    name = 'ralph.notifications'
    verbose_name = 'Notifiaction'

    def ready(self):
        if not settings.ENABLE_EMAIL_NOTIFICATION:
            return
        models = [
            'data_center.DataCenterAsset',
            'data_center.Cluster',
            'virtual.VirtualServer',
            'virtual.CloudProject',
        ]
        for model in models:
            post_save.connect(
                receiver=send_notification_for_model,
                sender=model
            )
