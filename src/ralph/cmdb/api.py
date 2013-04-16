#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ReST CMDB API
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

# Monkeypatch Tastypie
# fix in https://github.com/toastdriven/django-tastypie/pull/863
from ralph.cmdb.monkey import method_check
from tastypie.resources import Resource
Resource.method_check = method_check

from django.conf import settings
from tastypie.authentication import ApiKeyAuthentication
from tastypie.constants import ALL, ALL_WITH_RELATIONS
from tastypie.fields import ForeignKey as TastyForeignKey
from tastypie.resources import ModelResource as MResource
from tastypie.throttle import CacheThrottle

from ralph.account.api_auth import RalphAuthorization
from ralph.account.models import Perm
from ralph.cmdb.models import (
    CI,
    CIType,
    CIChange,
    CIChangeCMDBHistory,
    CIChangeGit,
    CIChangePuppet,
    CIChangeZabbixTrigger,
    CILayer,
    CIRelation,
)
from ralph.cmdb import models as db
from ralph.cmdb.models_ci import CIOwner, CIOwnershipType
from ralph.cmdb.models_audits import get_login_from_owner_name

THROTTLE_AT = settings.API_THROTTLING['throttle_at']
TIMEFRAME = settings.API_THROTTLING['timeframe']
EXPIRATION = settings.API_THROTTLING['expiration']


class BusinessLineResource(MResource):
    class Meta:
        # has only name, so skip content_object info
        queryset = CI.objects.filter(
            type__id=db.CI_TYPES.BUSINESSLINE.id).all()
        authentication = ApiKeyAuthentication()
        authorization = RalphAuthorization(
            required_perms=[
                Perm.read_configuration_item_info_generic,
            ]
        )
        filtering = {
            'added_manually': ALL,
            'barcode': ALL,
            'business_service': ALL,
            'created': ALL,
            'id': ALL,
            'modified': ALL,
            'name': ALL,
            'object_id': ALL,
            'pci_scope': ALL,
            'resource_uri': ALL,
            'state': ALL,
            'status': ALL,
            'technical_service': ALL,
            'uid': ALL,
            'zabbix_id': ALL,
        }
        excludes = ('cache_version', )
        list_allowed_methods = ['get']
        resource_name = 'businessline'
        throttle = CacheThrottle(
            throttle_at=THROTTLE_AT,
            timeframe=TIMEFRAME,
            expiration=EXPIRATION,
        )


class ServiceResource(MResource):
    class Meta:
        queryset = CI.objects.filter(type__id=db.CI_TYPES.SERVICE.id).all()
        authentication = ApiKeyAuthentication()
        authorization = RalphAuthorization(
            required_perms=[
                Perm.read_configuration_item_info_generic,
            ]
        )
        filtering = {
            'added_manually': ALL,
            'barcode': ALL,
            'business_service': ALL,
            'created': ALL,
            'modified': ALL,
            'name': ALL,
            'object_id': ALL,
            'pci_scope': ALL,
            'resource_uri': ALL,
            'state': ALL,
            'status': ALL,
            'technical_service': ALL,
            'uid': ALL,
            'zabbix_id': ALL,
        }
        excludes = ('cache_version', )
        list_allowed_methods = ['get']
        resource_name = 'service'
        throttle = CacheThrottle(
            throttle_at=THROTTLE_AT,
            timeframe=TIMEFRAME,
            expiration=EXPIRATION,
        )

    def dehydrate(self, bundle):
        # CMDB base info completed with content_object info
        attrs = ('external_key', 'location', 'state',
                 'it_person', 'it_person_mail', 'business_person',
                 'business_person_mail', 'business_line')
        ci = CI.objects.get(uid=bundle.data.get('uid'))
        for attr in attrs:
            bundle.data[attr] = getattr(ci.content_object, attr, '')
        return bundle


class CIRelationResource(MResource):
    class Meta:
        queryset = CIRelation.objects.all()
        authentication = ApiKeyAuthentication()
        authorization = RalphAuthorization(
            required_perms=[
                Perm.read_configuration_item_info_generic,
            ]
        )
        filtering = {
            'created': ALL,
            'id': ALL,
            'modified': ALL,
            'readonly': ALL,
            'resource_uri': ALL,
            'type': ALL,
        }
        excludes = ('cache_version', )
        list_allowed_methods = ['get']
        resource_name = 'cirelation'
        throttle = CacheThrottle(
            throttle_at=THROTTLE_AT,
            timeframe=TIMEFRAME,
            expiration=EXPIRATION,
        )

    def dehydrate(self, bundle):
        cirelation = CIRelation.objects.get(pk=bundle.data.get('id'))
        bundle.data['parent'] = cirelation.parent.id
        bundle.data['child'] = cirelation.child.id
        return bundle


class CIResource(MResource):
    class Meta:
        queryset = CI.objects.all()
        authentication = ApiKeyAuthentication()
        authorization = RalphAuthorization(
            required_perms=[
                Perm.read_configuration_item_info_generic,
            ]
        )
        list_allowed_methods = ['get']
        resource_name = 'ci'
        filtering = {
            'added_manually': ALL,
            'barcode': ('startswith', 'exact',),
            'business_service': ALL,
            'bussiness_owners': ALL,
            'cache_version': ALL,
            'created': ALL,
            'id': ALL,
            'layers': ALL_WITH_RELATIONS,
            'modified': ALL,
            'name': ('startswith', 'exact',),
            'object_id': ('exact',),
            'pci_scope': ('exact',),
            'resource_uri': ALL,
            'state': ALL,
            'status': ALL,
            'technical_owners': ALL,
            'technical_service': ALL,
            'type': ALL_WITH_RELATIONS,
            'uid': ALL,
            'zabbix_id': ALL,
        }
        throttle = CacheThrottle(
            throttle_at=THROTTLE_AT,
            timeframe=TIMEFRAME,
            expiration=EXPIRATION,
        )

    def dehydrate(self, bundle):
        ci = CI.objects.get(uid=bundle.data.get('uid'))
        bundle.data['type'] = {'name': ci.type.name, 'id': ci.type_id}
        for owner_type in (CIOwnershipType.technical,
                           CIOwnershipType.business):
            owners = CIOwner.objects.filter(
                ciownership__type=owner_type,
                ci=ci,
            )
            bundle.data["{}_owners".format(owner_type.name)] = []
            for technical_owner in owners:
                bundle.data["{}_owners".format(owner_type.name)].append(
                    {'username': get_login_from_owner_name(technical_owner)}
                )
        bundle.data['layers'] = []
        for layer in ci.layers.all():
            bundle.data['layers'].append({'name': layer.name, 'id': layer.id})
        return bundle


class CILayersResource(MResource):
    class Meta:
        queryset = CILayer.objects.all()
        authentication = ApiKeyAuthentication()
        authorization = RalphAuthorization(
            required_perms=[
                Perm.read_configuration_item_info_generic,
            ]
        )
        filtering = {
            'id': ALL,
            'name': ALL,
            'resource_uri': ALL,
        }
        excludes = ('icon', )
        list_allowed_methods = ['get']
        resourse_name = 'cilayers'
        excludes = ['cache_version', 'created', 'modified']
        throttle = CacheThrottle(
            throttle_at=THROTTLE_AT,
            timeframe=TIMEFRAME,
            expiration=EXPIRATION,
        )


class CIChangeResource(MResource):
    class Meta:
        queryset = CIChange.objects.all()
        authentication = ApiKeyAuthentication()
        authorization = RalphAuthorization(
            required_perms=[
                Perm.read_configuration_item_info_generic,
            ]
        )
        filtering = {
            'created': ALL,
            'external_key': ALL,
            'id': ALL,
            'message': ALL,
            'modified': ALL,
            'object_id': ALL,
            'priority': ALL,
            'registration_type': ALL,
            'resource_uri': ALL,
            'time': ALL,
            'type': ALL,
        }
        excludes = ('cache_version', )
        allowed_methods = ['get']
        resource_name = 'cichange'
        throttle = CacheThrottle(
            throttle_at=THROTTLE_AT,
            timeframe=TIMEFRAME,
            expiration=EXPIRATION,
        )


class CIChangeZabbixTriggerResource(MResource):
    class Meta:
        queryset = CIChangeZabbixTrigger.objects.all()
        authentication = ApiKeyAuthentication()
        authorization = RalphAuthorization(
            required_perms=[
                Perm.read_configuration_item_info_generic,
            ]
        )
        filtering = {
            'comments': ALL,
            'created': ALL,
            'description': ALL,
            'host': ALL,
            'host_id': ALL,
            'id': ALL,
            'lastchange': ALL,
            'modified': ALL,
            'priority': ALL,
            'resource_uri': ALL,
            'status': ALL,
            'trigger_id': ALL,
        }
        excludes = ('cache_version', )
        list_allowed_methods = ['get', 'post']
        resource_name = 'cichangezabbixtrigger'
        throttle = CacheThrottle(
            throttle_at=THROTTLE_AT,
            timeframe=TIMEFRAME,
            expiration=EXPIRATION,
        )


class CIChangeGitResource(MResource):
    class Meta:
        queryset = CIChangeGit.objects.all()
        authentication = ApiKeyAuthentication()
        authorization = RalphAuthorization(
            required_perms=[
                Perm.read_configuration_item_info_git,
            ]
        )
        filtering = {
            'author': ALL,
            'changeset': ALL,
            'comment': ALL,
            'created': ALL,
            'file_paths': ALL,
            'id': ALL,
            'modified': ALL,
            'resource_uri': ALL,
            'time': ALL,
        }
        excludes = ('cache_version', )
        list_allowed_methods = ['get', 'post']
        resource_name = 'cichangegit'
        throttle = CacheThrottle(
            throttle_at=THROTTLE_AT,
            timeframe=TIMEFRAME,
            expiration=EXPIRATION,
        )


class CIChangePuppetResource(MResource):
    class Meta:
        queryset = CIChangePuppet.objects.all()
        authentication = ApiKeyAuthentication()
        authorization = RalphAuthorization(
            required_perms=[
                Perm.read_configuration_item_info_puppet,
            ]
        )
        filtering = {
            'configuration_version': ALL,
            'created': ALL,
            'host': ALL,
            'id': ALL,
            'kind': ALL,
            'modified': ALL,
            'resource_uri': ALL,
            'status': ALL,
            'time': ALL,
        }
        excludes = ('cache_version', )
        list_allowed_methods = ['get', 'post']
        resource_name = 'cichangepuppet'
        throttle = CacheThrottle(
            throttle_at=THROTTLE_AT,
            timeframe=TIMEFRAME,
            expiration=EXPIRATION,
        )


class CIChangeCMDBHistoryResource(MResource):
    ci = TastyForeignKey(CIResource, 'ci')

    class Meta:
        queryset = CIChangeCMDBHistory.objects.all()
        authentication = ApiKeyAuthentication()
        authorization = RalphAuthorization(
            required_perms=[
                Perm.read_configuration_item_info_generic,
            ]
        )
        filtering = {
            'ci': ALL,
            'comment': ALL,
            'created': ALL,
            'field_name': ALL,
            'id': ALL,
            'modified': ALL,
            'new_value': ALL,
            'old_value': ALL,
            'resource_uri': ALL,
            'time': ALL,
        }
        excludes = ('cache_version', )
        list_allowed_methods = ['get']
        resource_name = 'cichangecmdbhistory'
        throttle = CacheThrottle(
            throttle_at=THROTTLE_AT,
            timeframe=TIMEFRAME,
            expiration=EXPIRATION,
        )


class CITypesResource(MResource):
    class Meta:
        queryset = CIType.objects.all()
        authentication = ApiKeyAuthentication()
        authorization = RalphAuthorization(
            required_perms=[
                Perm.read_configuration_item_info_generic,
            ]
        )
        filtering = {
            'id': ALL,
            'name': ALL,
            'resource_uri': ALL,
        }
        list_allowed_methods = ['get']
        resourse_name = 'citypes'
        excludes = ['cache_version', 'created', 'modified']
        throttle = CacheThrottle(
            throttle_at=THROTTLE_AT,
            timeframe=TIMEFRAME,
            expiration=EXPIRATION,
        )


class CIOwnersResource(MResource):
    class Meta:
        queryset = CIOwner.objects.all()
        authentication = ApiKeyAuthentication()
        authorization = RalphAuthorization(
            required_perms=[
                Perm.read_configuration_item_info_generic,
            ]
        )
        list_allowed_methods = ['get']
        filtering = {
            'cache_version': ALL,
            'created': ALL,
            'email': ALL,
            'first_name': ALL,
            'id': ALL,
            'last_name': ALL,
            'modified': ALL,
            'resource_uri': ALL,

        }
        excludes = ('cache_version', )
        resource_name = 'ciowners'
        throttle = CacheThrottle(
            throttle_at=THROTTLE_AT,
            timeframe=TIMEFRAME,
            expiration=EXPIRATION,
        )
