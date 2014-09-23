#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging

from django.conf import settings
from keystoneclient.v2_0 import client
from lck.django.common import nested_commit_on_success

from ralph.util import plugin
from ralph.discovery.models import Device, DeviceType


logger = logging.getLogger(__name__)

LIMIT = 1000000


@nested_commit_on_success
def save_tenant(tenant_id, tenant_name, model_name):
    """
    Saves single tenant as device with cloud_server model type.
    """
    dev = Device.create(
        model_name=model_name,
        model_type=DeviceType.cloud_server,
        sn='openstack-{}'.format(tenant_id)
    )
    dev.name = tenant_name
    dev.save()
    return dev


def get_tenants_list(site):
    """
    Returns list of tenants from OpenStack.
    """
    keystone_client = client.Client(
        username=site['USERNAME'],
        password=site['PASSWORD'],
        tenant_name=site['TENANT_NAME'],
        auth_url=site['AUTH_URL'],
    )
    return keystone_client.tenants.list(limit=LIMIT)


@plugin.register(chain='openstack')
def openstack(**kwargs):
    if settings.OPENSTACK_SITES is None:
        return False, 'not configured.', kwargs
    tenants_set = set()
    for site in settings.OPENSTACK_SITES:
        # add suffix to model name if defined
        model_suffix = site.get('MODEL_SUFFIX', '')
        model_name = 'OpenStack Tenant'
        if model_suffix:
            model_name = ' '.join((model_name, model_suffix.strip()))
        tenants = get_tenants_list(site)
        for tenant in tenants:
            save_tenant(tenant.id, tenant.name, model_name)
            tenants_set.add(tenant.id)
        logger.info('Saved {} tenants from {}'.format(
            len(tenants), site['DESCRIPTION'],
        ))
    return True, '{} OpenStack Tenants saved'.format(len(tenants_set)), kwargs
