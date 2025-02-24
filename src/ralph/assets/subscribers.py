# -*- coding: utf-8 -*-
import logging

import pyhermes
from django.conf import settings
from django.contrib.auth import get_user_model

from ralph.assets.models.assets import (
    BusinessSegment,
    Environment,
    ProfitCenter,
    Service,
    ServiceEnvironment
)
from ralph.assets.models.base import BaseObject

logger = logging.getLogger(__name__)

ACTION_TYPE = "PROCESS_HERMES_UPDATE_SERVICE_EVENT"


def _update_service_owners(service, business_owners, technical_owners):
    """
    Update business and technical owners for selected service.

    Args:
        service: Service
        business_owners: dict of owners
        technical_owners: dict of owners
    """
    business_owners = get_user_model().objects.filter(
        username__in=[i["username"] for i in business_owners]
    )
    technical_owners = get_user_model().objects.filter(
        username__in=[i["username"] for i in technical_owners]
    )
    service.business_owners.set(business_owners)
    service.technical_owners.set(technical_owners)


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
        ServiceEnvironment.objects.create(service=service, environment_id=env_id)
    for env_id in to_delete:
        service_env = ServiceEnvironment.objects.get(
            service=service, environment_id=env_id
        )
        if BaseObject.objects.filter(service_env=service_env).exists():
            logger.error(
                "Can not delete service environment - it has assigned some base objects",  # noqa: E501
                extra={
                    "action_type": ACTION_TYPE,
                    "service_uid": service.uid,
                    "service_name": service.name,
                },
            )
            return False
        service_env.delete()

    return True


def _update_area(service, area_name):
    if not service.business_segment or service.business_segment.name != area_name:
        service.business_segment = BusinessSegment.objects.get_or_create(
            name=area_name
        )[0]


def _update_profit_center(service, profit_center_name):
    if not service.profit_center or service.profit_center.name != profit_center_name:
        service.profit_center = ProfitCenter.objects.get_or_create(
            name=profit_center_name
        )[0]


@pyhermes.subscriber(topic=settings.HERMES_SERVICE_TOPICS["CREATE"])
@pyhermes.subscriber(topic=settings.HERMES_SERVICE_TOPICS["UPDATE"])
@pyhermes.subscriber(topic=settings.HERMES_SERVICE_TOPICS["REFRESH"])
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
            ],
            'area': {
                'name': 'area name',
                'profitCenter': 'profit center name',
            }
        }
    """
    try:
        service, _ = Service.objects.update_or_create(
            uid=service_data["uid"],
            defaults={
                "name": service_data["name"],
            },
        )
    except Exception as e:
        logger.exception(
            e,
            extra={
                "action_type": ACTION_TYPE,
                "service_uid": service_data["uid"],
                "service_name": service_data["name"],
            },
        )
    else:
        _update_service_owners(
            service=service,
            business_owners=service_data["businessOwners"],
            technical_owners=service_data["technicalOwners"],
        )
        if service_data.get("area"):
            _update_area(service, service_data["area"]["name"])
            if service_data["area"].get("profitCenter"):
                _update_profit_center(service, service_data["area"]["profitCenter"])
        update_envs = _update_service_environments(
            service=service, environments=service_data["environments"]
        )
        if update_envs:
            service.active = service_data["isActive"]
            service.save()

        logger.info(
            "Synced service `{}` with UID `{}`.".format(
                service_data["name"], service_data["uid"]
            ),
            extra={
                "action_type": ACTION_TYPE,
                "service_uid": service_data["uid"],
                "service_name": service_data["name"],
            },
        )


@pyhermes.subscriber(topic=settings.HERMES_SERVICE_TOPICS["DELETE"])
def delete_service_handler(service_data):
    """
    Set service active to False if service deleted.
    """
    try:
        service_envs = ServiceEnvironment.objects.filter(
            service__uid=service_data["uid"]
        )
        if BaseObject.objects.filter(service_env__in=service_envs).exists():
            logger.error(
                "Can not delete service - it has assigned some base objects",
                extra={
                    "action_type": ACTION_TYPE,
                    "service_uid": service_data["uid"],
                    "service_name": service_data["name"],
                },
            )
            return

        Service.objects.filter(uid=service_data["uid"]).update(active=False)
    except Exception as e:
        logger.exception(
            e,
            extra={
                "action_type": ACTION_TYPE,
                "service_uid": service_data["uid"],
                "service_name": service_data["name"],
            },
        )
    else:
        logger.info(
            "Service `{}` with UID `{}` deleted.".format(
                service_data["name"], service_data["uid"]
            ),
            extra={
                "action_type": ACTION_TYPE,
                "service_uid": service_data["uid"],
                "service_name": service_data["name"],
            },
        )
