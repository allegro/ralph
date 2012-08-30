#!/usr/bin/env python
# -*- coding: utf-8 -*-

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

from ralph.deployment.models import Deployment


class DeploymentResource(MResource):
    venture = fields.ForeignKey('ralph.business.api.VentureResource', 'venture', null=True)
    role = fields.ForeignKey('ralph.business.api.RoleResource', 'venture_role', null=True)
    device = fields.ForeignKey('ralph.discovery.api.DevResource', 'device')

    class Meta:
        queryset = Deployment.objects.all()
        authentication = ApiKeyAuthentication()
        authorization = DjangoAuthorization()
        filtering = {
            'id': ALL,
            'created': ALL,
            'modified': ALL,
            'status_lastchanged': ALL,
            'issue_key': ALL,
            'user': ALL_WITH_RELATIONS,
            'device': ALL_WITH_RELATIONS,
            'mac': ALL,
            'status': ALL,
            'ip': ALL,
            'hostname': ALL,
            'img_path': ALL,
            'kickstart_path': ALL,
            'venture': ALL_WITH_RELATIONS,
            'venture_role': ALL_WITH_RELATIONS,
        }
        excludes = ('save_priorities', 'max_save_priority',)
        cache = SimpleCache()
        limit = 10
