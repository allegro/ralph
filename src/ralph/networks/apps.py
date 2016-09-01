from django.conf import settings
from django.db.models.signals import post_delete, post_save

from ralph.apps import RalphAppConfig


class Networks(RalphAppConfig):
    name = 'ralph.networks'

    def ready(self):
        if not settings.ENABLE_DNSAAS_INTEGRATION:
            return
        from ralph.networks.receivers import (
            delete_dns_record,
            update_dns_record
        )
        ip_model = self.get_model('IPAddress')
        post_save.connect(
            receiver=update_dns_record,
            sender=ip_model
        )
        post_delete.connect(
            receiver=delete_dns_record,
            sender=ip_model,
        )
