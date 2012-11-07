#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.utils import simplejson
from django import forms
from ajax_select.fields import AutoCompleteSelectField

from ralph.cmdb.views import BaseCMDBView
from ralph.cmdb.models import CI, CIRelation, CI_TYPES, CI_RELATION_TYPES
from ralph.discovery.models import DeviceModel, DeviceType
from django.http import HttpResponse
import pygraph


class SearchImpactForm(forms.Form):
    depth = forms.CharField(max_length=100)
    ci = AutoCompleteSelectField(
        'ci', required=True,
        plugin_options={'minLength': 3},
    )


class Graphs(BaseCMDBView):
    template_name = 'cmdb/graphs.html'

    output = ''

    def get_context_data(self, **kwargs):
        ret = super(BaseCMDBView, self).get_context_data(**kwargs)
        form = SearchImpactForm(initial=self.get_initial())
        ret.update(dict(
            form=form,
            output=self.output
        ))
        return ret

    def get_initial(self):
        return dict(
            depth=3,
            ci=3313,
        )

    @staticmethod
    def get_ajax(self):
        root = CI.objects.filter(name='DC2')[0]
        models_to_display = [
            x.id for x in DeviceModel.objects.filter(type__in=[DeviceType.rack.id])
        ]
        relations = [dict(
            parent=x.parent.id, child=x.child.id, parent_name=x.parent.name, child_name=x.child.name,
            )
            for x in CIRelation.objects.filter(parent=root, child__type=CI_TYPES.DEVICE.id) if
            x.child.content_object.model and x.child.content_object.model.id in models_to_display]
        nodes = dict()
        for x in relations:
            nodes[x.get('parent')] = x.get('parent_name')
            nodes[x.get('child')] = x.get('child_name')

        response_dict = dict(
                nodes=nodes.items(), relations=relations)
        return HttpResponse(
            simplejson.dumps(response_dict),
            mimetype='application/json',
        )

    def get(self, *args, **kwargs):
        ci_id = self.request.GET.get('ci')
        depth = self.request.GET.get('depth')
        if ci_id and depth:
            pass
            #self.calculate_dependencies(ci_id, depth)
            #self.find(ci_id)
        self.output = 'output'
        return super(BaseCMDBView, self).get(*args, **kwargs)


class ImpactCalculator(object):
    graph = None

    def __init__(self):
        self.build_graph()

    def calculate_dependencies(self, ci_id, depth):
        ci = CI.objects.get(id=ci_id)
        # everything it contains is marked failed.
        contains_cis = CIRelation.objects.filter(
            parent__id=ci.id, type=CI_RELATION_TYPES.CONTAINS
        )
        # everything that depend on this ci is marked failed as well.
        is_required_by = CIRelation.objects.filter(
            child__id=ci.id, type=CI_RELATION_TYPES.REQUIRES
        )

    def build_graph(self):
        allci = CI.objects.all().values('pk')
        relations = CIRelation.objects.all().values('parent_id', 'child_id')
        nodes = [x['pk'] for x in allci]
        edges = [(x['parent_id'], x['child_id']) for x in relations]
        self.graph = pygraph.classes.digraph()
        self.graph.add_nodes(nodes)
        for edge in edges:
            self.graph.add_edge(edge)

    def find(self, ci_id):
        ci = CI.objects.get(id=ci_id)
        pass
