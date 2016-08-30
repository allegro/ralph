from django.conf import settings
from django.db.models.signals import post_save

from ralph.apps import RalphAppConfig


class Networks(RalphAppConfig):
    name = 'ralph.networks'

    def ready(self):
        if not settings.ENABLE_DNSAAS_INTEGRATION:
            return
        from ralph.networks.receivers import send_ipaddress_to_dnsaas
        post_save.connect(
            receiver=send_ipaddress_to_dnsaas,
            sender=self.get_model('IPAddress')
        )
