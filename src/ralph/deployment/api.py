#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.conf import settings
from tastypie import fields
from tastypie.authentication import ApiKeyAuthentication
from tastypie.cache import SimpleCache
from tastypie.constants import ALL, ALL_WITH_RELATIONS
from tastypie.resources import ModelResource as MResource
from tastypie.throttle import CacheThrottle

from ralph.account.api_auth import RalphAuthorization
from ralph.account.models import Perm
from ralph.deployment.models import Deployment

THROTTLE_AT = settings.API_THROTTLING['throttle_at']
TIMEFRAME = settings.API_THROTTLING['timeframe']
EXPIRATION = settings.API_THROTTLING['expiration']


class DeploymentResource(MResource):
    venture = fields.ForeignKey(
        'ralph.business.api.VentureResource',
        'venture',
        null=True,
    )
    role = fields.ForeignKey(
        'ralph.business.api.RoleResource',
        'venture_role',
        null=True,
    )
    device = fields.ForeignKey('ralph.discovery.api.DevResource', 'device')

    class Meta:
        queryset = Deployment.objects.all()
        authentication = ApiKeyAuthentication()
        authorization = RalphAuthorization(
            required_perms=[
                Perm.read_deployment,
            ]
        )
        filtering = {
            'created': ALL,
            'device': ALL_WITH_RELATIONS,
            'done_plugins': ALL,
            'hostname': ALL,
            'id': ALL,
            'img_path': ALL,
            'ip': ALL,
            'is_running': ALL,
            'issue_key': ALL,
            'kickstart_path': ALL,
            'mac': ALL,
            'modified': ALL,
            'status': ALL,
            'status_lastchanged': ALL,
            'user': ALL_WITH_RELATIONS,
            'venture': ALL_WITH_RELATIONS,
            'venture_role': ALL_WITH_RELATIONS,
        }
        excludes = ('save_priorities', 'max_save_priority', 'cache_version', )
        cache = SimpleCache()
        throttle = CacheThrottle(
            throttle_at=THROTTLE_AT,
            timeframe=TIMEFRAME,
            expiration=EXPIRATION,
        )
