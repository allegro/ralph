#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.utils import simplejson
from django import forms
from django.http import HttpResponse
from ajax_select.fields import AutoCompleteSelectField

from ralph.cmdb.models import CI, CIRelation, CI_TYPES, CI_RELATION_TYPES
from ralph.discovery.models import DeviceModel, DeviceType
from ralph.cmdb.views import BaseCMDBView, get_icon_for

import pygraph
from pygraph.algorithms.searching import breadth_first_search


class SearchImpactForm(forms.Form):
    ci = AutoCompleteSelectField(
        'ci', required=True,
        plugin_options={'minLength': 3}
    )

total_tree = dict()


def search_tree(tree, root):
    # Draw compositon three of given devices
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


class GraphsThree(BaseCMDBView):
    template_name = 'cmdb/graphs_three.html'

    @staticmethod
    def get_ajax(self):
        root = CI.objects.filter(name='DC2')[0]
        search_tree(total_tree, root)

        response_dict = total_tree

        return HttpResponse(
            simplejson.dumps(response_dict),
            mimetype='application/json',
        )


class Graphs(BaseCMDBView):
    template_name = 'cmdb/graphs.html'
    rows = ''
    graph_data = {}

    def get_context_data(self, *args, **kwargs):
        ret = super(Graphs, self).get_context_data(**kwargs)
        form = SearchImpactForm(initial=self.get_initial())
        ret.update(dict(
            form=form,
            rows=self.rows,
            graph_data=simplejson.dumps(self.graph_data),
        ))
        return ret

    def get_initial(self):
        return dict(
            ci=self.request.GET.get('ci'),
        )

    def get(self, *args, **kwargs):
        ci_id = self.request.GET.get('ci')
        self.rows = []
        if ci_id:
            ci_names = dict([(x.id, x.name) for x in CI.objects.all()])
            i = ImpactCalculator()
            st, pre = i.find_affected_nodes(int(ci_id))
            nodes = [(
                key, ci_names[key],
                get_icon_for(CI.objects.get(pk=key))) for key in st.keys()]
            relations = [dict(
                child=x,
                parent=st.get(x),
                parent_name=ci_names[x],
                type=CIRelation.objects.filter(
                    child__id=x, parent__id=st.get(x)
                )[0].type,
                child_name=ci_names[st.get(x)])
                for x in st.keys() if x and st.get(x)]
            self.graph_data = dict(
                nodes=nodes, relations=relations)
            self.rows = [dict(
                icon=get_icon_for(CI.objects.get(pk=x)),
                ci=CI.objects.get(pk=x)) for x in pre]
        return super(BaseCMDBView, self).get(*args, **kwargs)


class ImpactCalculator(object):
    graph = None

    def __init__(self, relation_types=[]):
        default_relation_types = [
            CI_RELATION_TYPES.CONTAINS.id,
            CI_RELATION_TYPES.REQUIRES.id,
            CI_RELATION_TYPES.HASROLE.id,
        ]
        if not relation_types:
            self.relation_types = default_relation_types
        else:
            self.relation_types = relation_types
        self.build_graph()

    def find_affected_nodes(self, ci_id):
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
        self.graph = pygraph.classes.digraph.digraph()
        self.graph.add_nodes([x['pk'] for x in allci])
        for x in relations:
            self.graph.add_edge((x['parent_id'], x['child_id']))

