#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from collections import defaultdict
from itertools import chain

import pygraph
from pygraph.algorithms.searching import breadth_first_search
from pygraph.classes.exceptions import AdditionError

from ralph.cmdb.models import CI, CIRelation, CI_TYPES, CI_RELATION_TYPES


class ImpactCalculator(object):

    def __init__(self, root_ci, relation_types=[]):
        self.root_ci = root_ci
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

    def cache_relations(self):
        """Pre-load cache of all contains-relations, to be more effective
        across instances than querysets"""
        self.cached_relations = defaultdict(list)
        for relation in CIRelation.objects.values(
                'parent_id', 'child_id', 'type', 'id').filter(
                type=CI_RELATION_TYPES.CONTAINS.id):
            self.cached_relations[relation.get('parent_id')].append({
                'parent': relation.get('parent_id'),
                'child': relation.get('child_id'),
                'type': relation.get('type'),
                'id': relation.get('id'),
            })

    def get_all_children(self):
        """Returns all down-level children that matches CONTAINS relation"""
        self.cache_relations()
        self.visited_nodes = set()
        return self.get_all_children_rec(self.root_ci.id)

    def get_all_children_rec(self, node):
        stack = [node]
        visited = {node}
        while stack:
            node = stack.pop()
            for child in self.cached_relations[node]:
                if child['id'] in visited:
                    continue
                yield child
                visited.add(node)
                stack.append(child['id'])

    def find_affected_nodes(self, ci_id):
        try:
            search_tree, pre = breadth_first_search(self.graph, ci_id)
        except KeyError:
            return []
        return (search_tree, pre)

    def add_edge(self, type_, parent_id, child_id):
        if type_ == CI_RELATION_TYPES.CONTAINS.id:
            # the only relation which we can traverse going straight
            from_ = parent_id
            to = child_id
        else:
            # opposite direction for graph traversal.
            from_ = child_id
            to = parent_id
        try:
            # the only relation which we can traverse going straight
            self.graph.add_edge((from_, to), attrs=(type_,))
        except AdditionError:
            # ignore duplicated relations(types) in graph
            pass

    def build_graph(self):
        # get all down-level children
        ci_contains = self.get_all_children()
        # get one level up parents
        ci_is_part_of = CIRelation.objects.filter(child__id=self.root_ci.id)
        ci_is_required = CIRelation.objects.filter(
            # get children and parent one level up/down.
            type=CI_RELATION_TYPES.REQUIRES.id,
            child=self.root_ci,
        )
        ci_requires = CIRelation.objects.filter(
            # get children and parent one level up/down.
            type=CI_RELATION_TYPES.REQUIRES.id,
            parent=self.root_ci,
        )
        ci_is_role = CIRelation.objects.filter(
            type=CI_RELATION_TYPES.HASROLE.id,
            child=self.root_ci,
        )
        ci_has_role = CIRelation.objects.filter(
            type=CI_RELATION_TYPES.HASROLE.id,
            parent=self.root_ci,
        )
        ci_service = CIRelation.objects.filter(
            # get venture node belongs to, and service venture belongs to.
            type=CI_RELATION_TYPES.CONTAINS.id,
            child__child=self.root_ci,
            parent__type=CI_TYPES.SERVICE.id,
            child__type=CI_TYPES.VENTURE.id,
        )
        self.graph = pygraph.classes.graph.graph()
        self.graph.add_nodes(CI.objects.values_list('pk', flat=True))

        for relation in ci_contains:
            parent = relation['parent']
            child = relation['child']
            type_ = relation['type']
            self.add_edge(type_, parent, child)

        for relation in chain(
            ci_is_part_of,
            ci_is_required,
            ci_requires,
            ci_is_role,
            ci_has_role,
            ci_service,
        ):
            self.add_edge(relation.type, relation.parent_id, relation.child_id)
