#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import pygraph
from pygraph.algorithms.searching import breadth_first_search
from pygraph.classes.exceptions import AdditionError

from ralph.cmdb.models import CI, CIRelation, CI_TYPES, CI_RELATION_TYPES
from ralph.discovery.models import DeviceModel, DeviceType


def search_tree(tree, root):
    # Draw compositon tree of given devices
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
    return tree


class ImpactCalculator(object):

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
        ).values('parent_id', 'child_id', 'type')
        self.graph = pygraph.classes.digraph.digraph()
        self.graph.add_nodes([ci['pk'] for ci in allci])
        for relation in relations:
            if relation['type'] == CI_RELATION_TYPES.CONTAINS.id:
                # the only relation which we can traverse going straight
                parent = relation['parent_id']
                child = relation['child_id']
            else:
                # opposite direction for graph traversal.
                parent = relation['child_id']
                child = relation['parent_id']
            try:
                self.graph.add_edge((parent, child), attrs=(relation['type'],))
            except AdditionError:
                # ignore duplicated relations(types) in graph
                pass


