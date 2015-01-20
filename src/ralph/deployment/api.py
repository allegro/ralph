#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.conf import settings
from tastypie import fields
from tastypie import http
from tastypie.authentication import ApiKeyAuthentication
from tastypie.authorization import DjangoAuthorization
from tastypie.bundle import Bundle
from tastypie.cache import SimpleCache
from tastypie.constants import ALL, ALL_WITH_RELATIONS
from tastypie.exceptions import ImmediateHttpResponse
from tastypie.resources import ModelResource as MResource
from tastypie.resources import Resource
from tastypie.throttle import CacheThrottle

from ralph.account.api_auth import RalphAuthorization
from ralph.account.models import Perm
from ralph.deployment.models import Deployment
from ralph.deployment.util import (
    change_ip_address, ChangeIPAddressError,
)

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


class IPAddressChange(object):

    __slots__ = ['current_ip_address', 'new_ip_address']

    def __init__(self, current_ip_address=None, new_ip_address=None):
        self.current_ip_address = current_ip_address
        self.new_ip_address = new_ip_address


class IPAddressChangeResource(Resource):
    current_ip_address = fields.CharField(attribute='current_ip_address')
    new_ip_address = fields.CharField(attribute='new_ip_address')

    def obj_create(self, bundle, **kwargs):
        try:
            change = IPAddressChange(**bundle.data)
        except TypeError:
            raise ImmediateHttpResponse(
                response=http.HttpBadRequest(
                    'Unexpected argument. Allowed arguments: '
                    'current_ip_address and new_ip_address'
                )
            )
        try:
            change_ip_address(**bundle.data)
        except ChangeIPAddressError as e:
            raise ImmediateHttpResponse(
                response=http.HttpBadRequest(e.message)
            )
        bundle.obj = change
        return bundle

    def detail_uri_kwargs(self, bundle_or_obj):
        kwargs = {}
        if isinstance(bundle_or_obj, Bundle):
            kwargs['pk'] = bundle_or_obj.obj.new_ip_address
        else:
            kwargs['pk'] = bundle_or_obj.new_ip_address
        return kwargs

    def deserialize(self, request, data, format='application/json'):
        try:
            return super(IPAddressChangeResource, self).deserialize(
                request, data, format=format,
            )
        except Exception as e:
            # if an exception occurred here it must be due to deserialization
            raise ImmediateHttpResponse(
                response=http.HttpBadRequest(e.message)
            )

    class Meta:
        resource_name = 'change-ip-address'
        object_class = IPAddressChange
        authentication = ApiKeyAuthentication()
        authorization = DjangoAuthorization()
        filtering = {}
        cache = SimpleCache()
        throttle = CacheThrottle(
            throttle_at=THROTTLE_AT,
            timeframe=TIMEFRAME,
            expiration=EXPIRATION,
        )
        allowed_methods = ['post']
