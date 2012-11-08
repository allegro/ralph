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
from pygraph.algorithms.searching import breadth_first_search


class SearchImpactForm(forms.Form):
    depth = forms.CharField(max_length=100)
    ci = AutoCompleteSelectField(
        'ci', required=True,
        plugin_options={'minLength': 3}
    )

total_tree = dict()


def search_tree(tree, root=CI.objects.filter(name='DC2')[0]):
    models_to_display = [
        x.id for x in DeviceModel.objects.filter(type__in=[
            DeviceType.switch.id,
            DeviceType.router.id,
            DeviceType.management.id,
            DeviceType.storage.id,
            DeviceType.rack.id,
            DeviceType.blade_server.id,
            DeviceType.data_center.id,
            DeviceType.virtual_server.id
        ])]
    relations = [dict(
        parent=x.parent.id, child=x.child.id, parent_name=x.parent.name,
        child_name=x.child.name)
        for x in CIRelation.objects.filter(parent=root, child__type=CI_TYPES.DEVICE.id) if
        x.child.content_object.model and x.child.content_object.model.id in models_to_display]

    tree['name'] = root.name
    tree['children'] = []
    for x in relations:
        new = dict(name=x.get('child'), children=[])
        tree['children'].append(new)
        search_tree(root=CI.objects.get(id=x.get('child')), tree=new)


class Graphs(BaseCMDBView):
    template_name = 'cmdb/graphs.html'

    rows = ''

    def get_context_data(self, **kwargs):
        ret = super(BaseCMDBView, self).get_context_data(**kwargs)
        form = SearchImpactForm(initial=self.get_initial())
        ret.update(dict(
            form=form,
            rows=self.rows
        ))
        return ret

    def get_initial(self):
        return dict(
            depth=3,
            ci=192010,
        )

    @staticmethod
    def get_ajax(self):
        root = CI.objects.filter(name='DC2')[0]
        search_tree(total_tree, root)

        response_dict = total_tree

        return HttpResponse(
            simplejson.dumps(response_dict),
            mimetype='application/json',
        )

    @staticmethod
    def get_ajax2(self):
        root = CI.objects.filter(name='DC2')[0]
        models_to_display = [
            x.id for x in DeviceModel.objects.filter(type__in=[DeviceType.rack.id])
        ]
        relations = [dict(
            parent=x.parent.id, child=x.child.id, parent_name=x.parent.name,
            child_name=x.child.name)
            for x in CIRelation.objects.filter(
                parent=root, child__type=CI_TYPES.DEVICE.id) if
            x.child.content_object.model and
            x.child.content_object.model.id in models_to_display]
        nodes = dict()
        for x in relations:
            nodes[x.get('parent')] = x.get('parent_name')
            nodes[x.get('child')] = x.get('child_name')

        response_dict = dict(
            nodes=nodes.items(), relations=relations
        )
        return HttpResponse(
            simplejson.dumps(response_dict),
            mimetype='application/json',
        )

    def get(self, *args, **kwargs):
        ci_id = self.request.GET.get('ci')
        depth = self.request.GET.get('depth')
        if ci_id and depth:
            i = ImpactCalculator()
            st, pre = i.find_affected_nodes(int(ci_id), depth)
            self.rows = [CI.objects.get(pk=x) for x in pre]
        else:
            self.rows = []
        return super(BaseCMDBView, self).get(*args, **kwargs)


class ImpactCalculator(object):
    graph = None

    def __init__(self, relation_types=[]):
        default_relation_types = [CI_RELATION_TYPES.CONTAINS, CI_RELATION_TYPES.REQUIRES]
        if not relation_types:
            self.relation_types = default_relation_types
        else:
            self.relation_types = relation_types
        self.build_graph()

    def find_affected_nodes(self, ci_id, depth):
        try:
            st, pre = breadth_first_search(self.graph, ci_id)
        except KeyError:
            return []
        return (st, pre)

    def build_graph(self):
        allci = CI.objects.all().values('pk')
        relations = CIRelation.objects.filter(
            type__in=self.relation_types
        ).values('parent_id', 'child_id')
        nodes = [x['pk'] for x in allci]
        edges = [(x['parent_id'], x['child_id']) for x in relations]
        self.graph = pygraph.classes.digraph.digraph()
        self.graph.add_nodes(nodes)
        for edge in edges:
            self.graph.add_edge(edge)

