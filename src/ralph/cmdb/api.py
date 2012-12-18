#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ReST CMDB API
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.conf import settings
from tastypie.authentication import ApiKeyAuthentication
from tastypie.authorization import DjangoAuthorization
from tastypie.constants import ALL, ALL_WITH_RELATIONS
from tastypie.fields import ForeignKey as TastyForeignKey
from tastypie.resources import ModelResource as MResource
from tastypie.throttle import CacheThrottle

from ralph.cmdb.models import (
    CI,
    CIChangeStatusOfficeIncident,
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
TIMEFREME = settings.API_THROTTLING['timeframe']
EXPIRATION = settings.API_THROTTLING['expiration']


class BusinessLineResource(MResource):
    class Meta:
        # has only name, so skip content_object info
        queryset = CI.objects.filter(
            type__id=db.CI_TYPES.BUSINESSLINE.id).all()
        authentication = ApiKeyAuthentication()
        authorization = DjangoAuthorization()
        list_allowed_methods = ['get']
        resource_name = 'businessline'
        throttle = CacheThrottle(throttle_at=THROTTLE_AT, timeframe=TIMEFREME,
                                 expiration=EXPIRATION)


class ServiceResource(MResource):
    class Meta:
        queryset = CI.objects.filter(type__id=db.CI_TYPES.SERVICE.id).all()
        authentication = ApiKeyAuthentication()
        authorization = DjangoAuthorization()
        list_allowed_methods = ['get']
        resource_name = 'service'
        throttle = CacheThrottle(throttle_at=THROTTLE_AT, timeframe=TIMEFREME,
                                 expiration=EXPIRATION)

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
        authorization = DjangoAuthorization()
        list_allowed_methods = ['get']
        resource_name = 'cirelation'
        throttle = CacheThrottle(throttle_at=THROTTLE_AT, timeframe=TIMEFREME,
                                 expiration=EXPIRATION)

    def dehydrate(self, bundle):
        cirelation = CIRelation.objects.get(pk=bundle.data.get('id'))
        bundle.data['parent'] = cirelation.parent.id
        bundle.data['child'] = cirelation.child.id
        return bundle


class CIResource(MResource):
    class Meta:
        queryset = CI.objects.all()
        authentication = ApiKeyAuthentication()
        authorization = DjangoAuthorization()
        list_allowed_methods = ['get']
        resource_name = 'ci'
        filtering = {
            'name': ('startswith', 'exact',),
            'barcode': ('startswith', 'exact',),
            'layers': ALL_WITH_RELATIONS,
            'object_id': ('exact',),
            'pci_scope': ('exact',),
            'type': ALL_WITH_RELATIONS,
            'technical_owners': ALL,
            'bussiness_owners': ALL,
        }
        throttle = CacheThrottle(throttle_at=THROTTLE_AT, timeframe=TIMEFREME,
                                 expiration=EXPIRATION)

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
        authorization = DjangoAuthorization()
        list_allowed_methods = ['get']
        resourse_name = 'cilayers'
        excludes = ['cache_version', 'created', 'modified']
        throttle = CacheThrottle(throttle_at=THROTTLE_AT, timeframe=TIMEFREME,
                                 expiration=EXPIRATION)


class CIChangeResource(MResource):
    class Meta:
        queryset = CIChange.objects.all()
        authentication = ApiKeyAuthentication()
        authorization = DjangoAuthorization()
        allowed_methods = ['get']
        resource_name = 'cichange'
        throttle = CacheThrottle(throttle_at=THROTTLE_AT, timeframe=TIMEFREME,
                                 expiration=EXPIRATION)


class CIChangeZabbixTriggerResource(MResource):
    class Meta:
        queryset = CIChangeZabbixTrigger.objects.all()
        authentication = ApiKeyAuthentication()
        authorization = DjangoAuthorization()
        list_allowed_methods = ['get', 'post']
        resource_name = 'cichangezabbixtrigger'
        throttle = CacheThrottle(throttle_at=THROTTLE_AT, timeframe=TIMEFREME,
                                 expiration=EXPIRATION)


class CIChangeStatusOfficeIncidentResource(MResource):
    class Meta:
        queryset = CIChangeStatusOfficeIncident.objects.all()
        authentication = ApiKeyAuthentication()
        authorization = DjangoAuthorization()
        list_allowed_methods = ['get', 'post']
        resource_name = 'cichangestatusofficeincident'
        throttle = CacheThrottle(throttle_at=THROTTLE_AT, timeframe=TIMEFREME,
                                 expiration=EXPIRATION)


class CIChangeGitResource(MResource):
    class Meta:
        queryset = CIChangeGit.objects.all()
        authentication = ApiKeyAuthentication()
        authorization = DjangoAuthorization()
        list_allowed_methods = ['get', 'post']
        resource_name = 'cichangegit'
        throttle = CacheThrottle(throttle_at=THROTTLE_AT, timeframe=TIMEFREME,
                                 expiration=EXPIRATION)


class CIChangePuppetResource(MResource):
    class Meta:
        queryset = CIChangePuppet.objects.all()
        authentication = ApiKeyAuthentication()
        authorization = DjangoAuthorization()
        list_allowed_methods = ['get', 'post']
        resource_name = 'cichangepuppet'
        throttle = CacheThrottle(throttle_at=THROTTLE_AT, timeframe=TIMEFREME,
                                 expiration=EXPIRATION)


class CIChangeCMDBHistoryResource(MResource):
    ci = TastyForeignKey(CIResource, 'ci')

    class Meta:
        queryset = CIChangeCMDBHistory.objects.all()
        authentication = ApiKeyAuthentication()
        authorization = DjangoAuthorization()
        list_allowed_methods = ['get']
        resource_name = 'cichangecmdbhistory'
        throttle = CacheThrottle(throttle_at=THROTTLE_AT, timeframe=TIMEFREME,
                                 expiration=EXPIRATION)


class CITypesResource(MResource):
    class Meta:
        queryset = CIType.objects.all()
        authentication = ApiKeyAuthentication()
        authorization = DjangoAuthorization()
        list_allowed_methods = ['get']
        resourse_name = 'citypes'
        excludes = ['cache_version', 'created', 'modified']
        throttle = CacheThrottle(throttle_at=THROTTLE_AT, timeframe=TIMEFREME,
                                 expiration=EXPIRATION)
