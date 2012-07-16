#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""ReST API for Ralph's business models
   ------------------------------------

Done with TastyPie."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from tastypie import fields
from tastypie.authentication import ApiKeyAuthentication
from tastypie.authorization import DjangoAuthorization
from tastypie.cache import SimpleCache
from tastypie.constants import ALL, ALL_WITH_RELATIONS
from tastypie.resources import ModelResource as MResource
from ralph.business.models import Venture, VentureRole


class VentureResource(MResource):
    devices = fields.ToManyField('ralph.discovery.api.DevResource', 'device')
    roles = fields.ToManyField('ralph.business.api.RoleResource', 'venturerole')

    class Meta:
        queryset = Venture.objects.all()
        authentication = ApiKeyAuthentication()
        authorization = DjangoAuthorization()
        filtering = {
            'id': ALL,
            'name': ALL,
            'symbol': ALL,
            'data_center': ALL_WITH_RELATIONS,
            'show_in_ralph': ALL,
        }
        excludes = ('save_priorities', 'max_save_priority',)
        cache = SimpleCache()
        limit = 10


class VentureLightResource(MResource):
    class Meta:
        queryset = Venture.objects.all()
        authentication = ApiKeyAuthentication()
        authorization = DjangoAuthorization()
        filtering = {
            'id': ALL,
            'name': ALL,
            'symbol': ALL,
            'data_center': ALL_WITH_RELATIONS,
            'show_in_ralph': ALL,
        }
        excludes = ('save_priorities', 'max_save_priority',)
        cache = SimpleCache()

    def dehydrate_resource_uri(self, bundle):
        uri = super(VentureLightResource, self).dehydrate_resource_uri(bundle)
        return uri.replace('venturelight', 'venture')


class RoleResource(MResource):
    venture = fields.ForeignKey(VentureResource, 'venture', null=True)
    parent = fields.ForeignKey('ralph.business.api.RoleResource',
        'parent', null=True)

    class Meta:
        queryset = VentureRole.objects.all()
        authentication = ApiKeyAuthentication()
        authorization = DjangoAuthorization()
        filtering = {
            'id': ALL,
            'name': ALL,
            'venture': ALL_WITH_RELATIONS,
        }
        excludes = ('save_priorities', 'max_save_priority',)
        cache = SimpleCache()
