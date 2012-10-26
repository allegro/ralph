#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.utils import simplejson

from ralph.cmdb.views import BaseCMDBView
from ralph.cmdb.models import CI, CIRelation
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
        relations = [ dict(parent=x.parent.id, child=x.child.id, parent_name=x.parent.name, child_name=x.child.name)
                for x in CIRelation.objects.filter(parent__type=2)]
        nodes = dict()
        for x in relations:
            nodes[x.get('parent')] = x.get('parent_name')
            nodes[x.get('child')] = x.get('child_name')

        response_dict = dict(nodes=nodes.items(), relations=relations)
        return HttpResponse(
            simplejson.dumps(response_dict),
            mimetype='application/json',
        )
