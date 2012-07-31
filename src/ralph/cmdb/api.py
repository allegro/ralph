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
from ralph.cmdb.models import CI, CIRelation,JiraService,JiraBusinessLine
from ralph.cmdb import models as db


class JiraBusinessLineResource(MResource):
    class Meta:
        queryset = JiraBusinessLine.objects.all()
        #not sure if needed instead -
        #queryset = CI.objects.filter(type=db.CI_TYPES.BUSINESSLINE.id).all()
        authentication = ApiKeyAuthentication()
        authorization = DjangoAuthorization()
        resource_name = 'businessline'


class JiraServiceResource(MResource):
    class Meta:
        queryset = JiraService.objects.all()
        #not sure if needed instead -
        #queryset = CI.objects.filter(type=db.CI_TYPES.SERVICE.id).all()
        authentication = ApiKeyAuthentication()
        authorization = DjangoAuthorization()
        resource_name = 'service'


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

