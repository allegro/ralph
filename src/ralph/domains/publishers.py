# -*- coding: utf-8 -*-
import pyhermes
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from threadlocals.threadlocals import get_current_user

from ralph.data_center.models.physical import DataCenterAsset
from ralph.data_center.models.virtual import Cluster
from ralph.domains.models import Domain


def _publish_domain_to_dnsaaas(domain):
    business_owners = (
        [domain.business_owner.username] if domain.business_owner else []
    )
    technical_owners = (
        [domain.technical_owner.username] if domain.technical_owner else []
    )
    domain_data = {
        'domain_name': domain.name,
        'service_name': domain.service.name if domain.service else None,
        'service_uid': domain.service.uid if domain.service else None,
        'business_owners': business_owners,
        'technical_owners': technical_owners,
    }
    return domain_data


if settings.DNSAAS_DOMAIN_SERVICE_UPDATE_TOPIC:
    @pyhermes.publisher(
        topic=settings.DNSAAS_DOMAIN_SERVICE_UPDATE_TOPIC,
        auto_publish_result=True
    )
    def publish_domain_data_to_dnsaas(obj):
        return _publish_domain_to_dnsaaas(obj)

    @receiver(post_save, sender=Domain)
    def post_save_domain(sender, instance, **kwargs):
        publish_domain_data_to_dnsaas(instance)
