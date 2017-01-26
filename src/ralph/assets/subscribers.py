# -*- coding: utf-8 -*-
import logging

import pyhermes

from django.conf import settings
from django.contrib.auth import get_user_model

from ralph.assets.models.assets import Environment, Service, ServiceEnvironment
from ralph.assets.models.base import BaseObject

logger = logging.getLogger(__name__)


def _update_service_owners(service, business_owners, technical_owners):
    """
    Update business and technical owners for selected service.

    Args:
        service: Service
        business_owners: dict of owners
        technical_owners: dict of owners
    """
    business_owners = get_user_model().objects.filter(
        username__in=[i['username'] for i in business_owners]
    )
    technical_owners = get_user_model().objects.filter(
        username__in=[i['username'] for i in technical_owners]
    )

    service.business_owners = business_owners
    service.technical_owners = technical_owners


def _update_service_environments(service, environments):
    """
    Add and removes environments for selcted service.

    Args:
        service: Service
        environments: list of environment names

    Returns:
        True if service environment updated
        False if can not delete ServiceEnvironment
    """
    new_envs = []
    for env_name in environments:
        new_envs.append(Environment.objects.get_or_create(name=env_name)[0])

    current = set([e.id for e in service.environments.all()])
    new = set([e.id for e in new_envs])
    to_delete = current - new
    to_add = new - current
    for env_id in to_add:
        ServiceEnvironment.objects.create(
            service=service,
            environment_id=env_id
        )
    for env_id in to_delete:
        service_env = ServiceEnvironment.objects.get(
            service=service, environment_id=env_id
        )
        if BaseObject.objects.filter(service_env=service_env).exists():
            logger.error(
                'Can not delete service environment - it has assigned some base objects',  # noqa: E501
                extra={
                    'service_uid': service.uid,
                    'service_env': service_env
                }
            )
            return False
        service_env.delete()

    return True


@pyhermes.subscriber(topic=settings.HERMES_SERVICE_TOPICS['CREATE'])
@pyhermes.subscriber(topic=settings.HERMES_SERVICE_TOPICS['UPDATE'])
@pyhermes.subscriber(topic=settings.HERMES_SERVICE_TOPICS['REFRESH'])
def update_service_handler(service_data):
    """
    Update information about Service from Hermes event.

    Add, update or set active to False if Service has deleted.

    Example 'service_data' structures:
        {
            'uid': 'service uid',
            'name': 'service name',
            'status': 'service status',
            'isActive': 'boolean if service is active',
            'environments': 'service environments',
            'businessOwners': [
                {'username': 'username'}
            ],
            'technicalOwners': [
                {'username': 'username'}
            ]
        }
    """
    try:
        service, _ = Service.objects.update_or_create(
            uid=service_data['uid'],
            defaults={
                'name': service_data['name'],
            }
        )
    except Exception as e:
        logger.exception(e, extra=service_data)
    else:
        _update_service_owners(
            service=service,
            business_owners=service_data['businessOwners'],
            technical_owners=service_data['technicalOwners']
        )
        update_envs = _update_service_environments(
            service=service,
            environments=service_data['environments']
        )
        if update_envs:
            service.active = service_data['isActive']
            service.save()

        logger.info(
            'Synced service `{}` with UID `{}`.'.format(
                service_data['name'], service_data['uid']
            ),
            extra=service_data
        )


@pyhermes.subscriber(topic=settings.HERMES_SERVICE_TOPICS['DELETE'])
def delete_service_handler(service_data):
    """
    Set service active to False if service deleted.
    """
    try:
        service_envs = ServiceEnvironment.objects.filter(
            service__uid=service_data['uid']
        )
        if BaseObject.objects.filter(service_env__in=service_envs).exists():
            logger.error(
                'Can not delete service - it has assigned some base objects',
                extra=service_data
            )
            return

        Service.objects.filter(uid=service_data['uid']).update(active=False)
    except Exception as e:
        logger.exception(e, extra=service_data)
    else:
        logger.info(
            'Service `{}` with UID `{}` deleted.'.format(
                service_data['name'], service_data['uid']
            ),
            extra=service_data
        )
