#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""ReST API for Ralph's business models
   ------------------------------------

Done with TastyPie."""

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
from ralph.business.models import (
    Venture,
    VentureRole,
    Department,
    RolePropertyType,
    RolePropertyTypeValue,
    RoleProperty,
    RolePropertyValue,
    BusinessSegment,
    ProfitCenter,
)


THROTTLE_AT = settings.API_THROTTLING['throttle_at']
TIMEFRAME = settings.API_THROTTLING['timeframe']
EXPIRATION = settings.API_THROTTLING['expiration']


class VentureResource(MResource):
    devices = fields.ToManyField('ralph.discovery.api.DevResource', 'device')
    roles = fields.ToManyField(
        'ralph.business.api.RoleResource',
        'venturerole',
    )
    department = fields.ForeignKey(
        'ralph.business.api.DepartmentResource',
        'department',
        null=True,
        full=True,
    )
    business_segment = fields.ForeignKey(
        'ralph.business.api.BusinessSegmentResource',
        'business_segment',
        null=True,
        full=True,
    )
    profit_center = fields.ForeignKey(
        'ralph.business.api.ProfitCenterResource',
        'profit_center',
        null=True,
        full=True,
    )

    class Meta:
        queryset = Venture.objects.all()
        authentication = ApiKeyAuthentication()
        authorization = RalphAuthorization(
            required_perms=[
                Perm.read_dc_structure,
            ]
        )
        filtering = {
            'created': ALL,
            'data_center': ALL_WITH_RELATIONS,
            'business_segment': ALL_WITH_RELATIONS,
            'profit_center': ALL_WITH_RELATIONS,
            'department': ALL_WITH_RELATIONS,
            'devices': ALL,
            'id': ALL,
            'is_infrastructure': ALL,
            'modified': ALL,
            'name': ALL,
            'path': ALL,
            'roles': ALL,
            'show_in_ralph': ALL,
            'symbol': ALL,
        }
        excludes = ('save_priorities', 'max_save_priority', 'cache_version', )
        cache = SimpleCache()
        throttle = CacheThrottle(
            throttle_at=THROTTLE_AT,
            timeframe=TIMEFRAME,
            expiration=EXPIRATION,
        )


class VentureLightResource(MResource):
    department = fields.ForeignKey(
        'ralph.business.api.DepartmentResource',
        'department',
        null=True,
        full=True,
    )

    class Meta:
        queryset = Venture.objects.all()
        authentication = ApiKeyAuthentication()
        authorization = RalphAuthorization(
            required_perms=[
                Perm.read_dc_structure,
            ]
        )
        filtering = {
            'created': ALL,
            'data_center': ALL_WITH_RELATIONS,
            'department': ALL,
            'id': ALL,
            'is_infrastructure': ALL,
            'modified': ALL,
            'name': ALL,
            'path': ALL,
            'show_in_ralph': ALL,
            'symbol': ALL,
        }
        excludes = ('save_priorities', 'max_save_priority', 'cache_version', )
        cache = SimpleCache()
        throttle = CacheThrottle(
            throttle_at=THROTTLE_AT,
            timeframe=TIMEFRAME,
            expiration=EXPIRATION,
        )

    def dehydrate_resource_uri(self, bundle):
        uri = super(VentureLightResource, self).dehydrate_resource_uri(bundle)
        return uri.replace('venturelight', 'venture')


class RoleResource(MResource):
    venture = fields.ForeignKey(VentureResource, 'venture', null=True)
    parent = fields.ForeignKey(
        'ralph.business.api.RoleResource',
        'parent',
        null=True,
    )
    devices = fields.ToManyField('ralph.discovery.api.DevResource', 'device')
    properties = fields.ToManyField('ralph.business.api.RolePropertyResource',
                                    'roleproperty', full=True)

    class Meta:
        queryset = VentureRole.objects.all()
        authentication = ApiKeyAuthentication()
        authorization = RalphAuthorization(
            required_perms=[
                Perm.read_dc_structure,
            ]
        )
        filtering = {
            'created': ALL,
            'devices': ALL,
            'id': ALL,
            'modified': ALL,
            'name': ALL,
            'parent': ALL,
            'path': ALL,
            'properties': ALL,
            'venture': ALL_WITH_RELATIONS,
        }
        excludes = ('save_priorities', 'max_save_priority', 'cache_version', )
        cache = SimpleCache()
        throttle = CacheThrottle(
            throttle_at=THROTTLE_AT,
            timeframe=TIMEFRAME,
            expiration=EXPIRATION,
        )


class RoleLightResource(MResource):
    venture = fields.ForeignKey(VentureResource, 'venture', null=True)
    parent = fields.ForeignKey(
        'ralph.business.api.RoleResource',
        'parent',
        null=True,
    )

    class Meta:
        queryset = VentureRole.objects.all()
        authentication = ApiKeyAuthentication()
        authorization = RalphAuthorization(
            required_perms=[
                Perm.read_dc_structure,
            ]
        )
        filtering = {
            'created': ALL,
            'id': ALL,
            'modified': ALL,
            'name': ALL,
            'parent': ALL,
            'path': ALL,
            'venture': ALL_WITH_RELATIONS,
        }
        excludes = ('save_priorities', 'max_save_priority', 'cache_version', )
        cache = SimpleCache()
        throttle = CacheThrottle(
            throttle_at=THROTTLE_AT,
            timeframe=TIMEFRAME,
            expiration=EXPIRATION,
        )

    def dehydrate_resource_uri(self, bundle):
        uri = super(RoleLightResource, self).dehydrate_resource_uri(bundle)
        return uri.replace('rolelight', 'role')


class DepartmentResource(MResource):

    class Meta:
        queryset = Department.objects.all()
        authentication = ApiKeyAuthentication()
        authorization = RalphAuthorization(
            required_perms=[
                Perm.read_dc_structure,
            ]
        )
        filtering = {
            'id': ALL,
            'name': ALL,
        }
        cache = SimpleCache()
        excludes = ('icon',)
        throttle = CacheThrottle(
            throttle_at=THROTTLE_AT,
            timeframe=TIMEFRAME,
            expiration=EXPIRATION,
        )


class RolePropertyTypeResource(MResource):

    class Meta:
        queryset = RolePropertyType.objects.all()
        authentication = ApiKeyAuthentication()
        authorization = RalphAuthorization(
            required_perms=[
                Perm.read_dc_structure,
            ]
        )
        filtering = {
            'id': ALL,
            'symbol': ALL,
        }
        cache = SimpleCache()
        throttle = CacheThrottle(
            throttle_at=THROTTLE_AT,
            timeframe=TIMEFRAME,
            expiration=EXPIRATION,
        )


class RolePropertyTypeValueResource(MResource):
    type = fields.ForeignKey(
        RolePropertyTypeResource,
        'type',
        null=True,
        full=True,
    )

    class Meta:
        queryset = RolePropertyTypeValue.objects.all()
        authentication = ApiKeyAuthentication()
        authorization = RalphAuthorization(
            required_perms=[
                Perm.read_dc_structure,
            ]
        )
        filtering = {
            'default': ALL,
            'id': ALL,
            'role': ALL,
            'symbol': ALL,
            'type': ALL,
            'value': ALL,
        }
        cache = SimpleCache()
        throttle = CacheThrottle(
            throttle_at=THROTTLE_AT,
            timeframe=TIMEFRAME,
            expiration=EXPIRATION,
        )


class RolePropertyResource(MResource):
    role = fields.ForeignKey(RoleResource, 'role', null=True)
    type = fields.ForeignKey(
        RolePropertyTypeResource,
        'type',
        null=True,
        full=True,
    )

    class Meta:
        queryset = RoleProperty.objects.all()
        authentication = ApiKeyAuthentication()
        authorization = RalphAuthorization(
            required_perms=[
                Perm.read_dc_structure,
            ]
        )
        filtering = {
            'default': ALL,
            'id': ALL,
            'role': ALL,
            'symbol': ALL,
            'type': ALL,
        }
        cache = SimpleCache()
        throttle = CacheThrottle(
            throttle_at=THROTTLE_AT,
            timeframe=TIMEFRAME,
            expiration=EXPIRATION,
        )


class RolePropertyValueResource(MResource):
    property = fields.ForeignKey(
        RolePropertyResource,
        'property',
        null=True,
        full=True,
    )
    device = fields.ForeignKey(
        'ralph.discovery.api.DevResource',
        'device',
        null=True,
    )

    class Meta:
        queryset = RolePropertyValue.objects.all()
        authentication = ApiKeyAuthentication()
        authorization = RalphAuthorization(
            required_perms=[
                Perm.read_dc_structure,
            ]
        )
        filtering = {
            'created': ALL,
            'device': ALL,
            'id': ALL,
            'modified': ALL,
            'property': ALL,
            'value': ALL,
        }
        excludes = ('cache_version', )
        cache = SimpleCache()
        throttle = CacheThrottle(
            throttle_at=THROTTLE_AT,
            timeframe=TIMEFRAME,
            expiration=EXPIRATION,
        )


class BusinessSegmentResource(MResource):

    class Meta:
        queryset = BusinessSegment.objects.all()
        authentication = ApiKeyAuthentication()
        authorization = RalphAuthorization(
            required_perms=[
                Perm.read_dc_structure,
            ]
        )
        filtering = {
            'id': ALL,
            'name': ALL,
        }
        cache = SimpleCache()
        throttle = CacheThrottle(
            throttle_at=THROTTLE_AT,
            timeframe=TIMEFRAME,
            expiration=EXPIRATION,
        )


class ProfitCenterResource(MResource):

    class Meta:
        queryset = ProfitCenter.objects.all()
        authentication = ApiKeyAuthentication()
        authorization = RalphAuthorization(
            required_perms=[
                Perm.read_dc_structure,
            ]
        )
        filtering = {
            'id': ALL,
            'name': ALL,
        }
        cache = SimpleCache()
        throttle = CacheThrottle(
            throttle_at=THROTTLE_AT,
            timeframe=TIMEFRAME,
            expiration=EXPIRATION,
        )
