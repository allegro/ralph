# -*- coding: utf-8 -*-
import logging

import pyhermes
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from ralph.domains.models import Domain


logger = logging.getLogger(__name__)


def _publish_domain_data(domain):
    owners = []
    if domain.business_owner:
        owners.append({
            'username': domain.business_owner.username,
            'ownership_type': settings.DOMAIN_OWNER_TYPE['BO'],
        })
    if domain.technical_owner:
        owners.append({
            'username': domain.technical_owner.username,
            'ownership_type': settings.DOMAIN_OWNER_TYPE['TO'],
        })

    if not owners:
        logger.debug('no owners for domain: {}'.format(domain.id))
        return {}

    domain_data = {
        'domain_name': domain.name,
        'owners': owners,
    }
    return domain_data


if settings.DOMAIN_DATA_UPDATE_TOPIC:
    @pyhermes.publisher(
        topic=settings.DOMAIN_DATA_UPDATE_TOPIC,
        auto_publish_result=True
    )
    def publish_domain_data(obj):
        return _publish_domain_data(obj)

    @receiver(post_save, sender=Domain)
    def post_save_domain(sender, instance, **kwargs):
        publish_domain_data(instance)
