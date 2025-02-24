# -*- coding: utf-8 -*-
from django.conf import settings

from ralph.apps import RalphAppConfig
from ralph.notifications.sender import send_notification_for_model
from ralph.signals import post_commit


class NotificationConfig(RalphAppConfig):
    name = "ralph.notifications"
    verbose_name = "Notifiaction"

    def ready(self):
        if not settings.ENABLE_EMAIL_NOTIFICATION:
            return
        models = [
            "data_center.DataCenterAsset",
            "data_center.Cluster",
            "virtual.VirtualServer",
            "virtual.CloudProject",
        ]
        for model in models:
            post_commit(send_notification_for_model, model)
