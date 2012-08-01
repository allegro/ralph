#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ReST CMDB API
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from tastypie.authentication import ApiKeyAuthentication
from tastypie.authorization import DjangoAuthorization
from tastypie.resources import ModelResource as MResource
from ralph.cmdb.models import CI, CIRelation
from ralph.cmdb import models as db


class BusinessLineResource(MResource):
    class Meta:
        # has only name, so skip content_object info
        queryset = CI.objects.filter(type__id=db.CI_TYPES.BUSINESSLINE.id).all()
        authentication = ApiKeyAuthentication()
        authorization = DjangoAuthorization()
        resource_name = 'businessline'


class ServiceResource(MResource):
    class Meta:
        queryset = CI.objects.filter(type__id=db.CI_TYPES.SERVICE.id).all()
        authentication = ApiKeyAuthentication()
        authorization = DjangoAuthorization()
        resource_name = 'service'

    def dehydrate(self, bundle):
        # CMDB base info completed with content_object info
        attrs = ('external_key', 'location', 'state', \
                'it_person','it_person_mail', 'business_person', \
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
        resource_name = 'cirelation'


class CIResource(MResource):
    class Meta:
        queryset = CI.objects.all()
        authentication = ApiKeyAuthentication()
        authorization = DjangoAuthorization()
        resource_name = 'ci'

