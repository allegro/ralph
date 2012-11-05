#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.utils import simplejson

from ralph.cmdb.views import BaseCMDBView
from ralph.cmdb.models import CI, CIRelation, CI_TYPES
from ralph.discovery.models import DeviceModel, DeviceType
from django.http import HttpResponse

class Graphs(BaseCMDBView):
    template_name = 'cmdb/graphs.html'

    def get_context_data(self, **kwargs):
        ret = super(BaseCMDBView, self).get_context_data(**kwargs)
        ret.update({
        })
        return ret

    @staticmethod
    def get_ajax(self):
        root = CI.objects.filter(name='DC2')[0]
        models_to_display = [ x.id for x in DeviceModel.objects.filter(type__in=[DeviceType.rack.id])]
        relations = [ dict(parent=x.parent.id, child=x.child.id, parent_name=x.parent.name, child_name=x.child.name,
            dupa=x.child.content_object.model.name)
                for x in CIRelation.objects.filter(parent=root, child__type=CI_TYPES.DEVICE.id) if
                x.child.content_object.model and x.child.content_object.model.id in models_to_display]
        nodes = dict()
        for x in relations:
            nodes[x.get('parent')] = x.get('parent_name')
            nodes[x.get('child')] = x.get('child_name')

        response_dict = dict(nodes=nodes.items(), relations=relations)
        return HttpResponse(
            simplejson.dumps(response_dict),
            mimetype='application/json',
        )
