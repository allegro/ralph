#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from collections import defaultdict
from itertools import chain

from django.db.models import Q
import pygraph
from pygraph.algorithms.searching import breadth_first_search
from pygraph.classes.exceptions import AdditionError

from ralph.cmdb.models import CI, CIRelation, CI_TYPES, CI_RELATION_TYPES
from ralph.discovery.models import DeviceModel, DeviceType


class ImpactCalculator(object):
    visited = []

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
        self.cached_relations = defaultdict(list)
        for x in CIRelation.objects.values('parent_id', 'child_id', 'type', 'id').filter(
                type=CI_RELATION_TYPES.CONTAINS.id):
            self.cached_relations[x.get('parent_id')].append({
                'parent': x.get('parent_id'),
                'child': x.get('child_id'),
                'type': x.get('type'),
                'id': x.get('id')
            })

    def get_contained_childs(self):
        self.cache_relations()
        return self.get_all_contains(self.root_ci.id)

    def get_all_contains(self, ci_id):
        if self.cached_relations[ci_id]:
            # already has been there
            return []
        affected = []
        for rel in self.cached_relations[ci_id]:
            affected.append(rel)
            affected.extend(self.get_all_contains(rel['child']))
        return affected

    def find_affected_nodes(self, ci_id):
        try:
            st, pre = breadth_first_search(self.graph, ci_id)
        except KeyError:
            return []
        return (st, pre)

    def build_graph(self):
        # get all down-level childs
        ci_contained = self.get_contained_childs()
        # get one level up parents
        ci_parented = CIRelation.objects.filter(child__id=self.root_ci.id)

        ci_is_required = CIRelation.objects.filter(
            # get children and parent one level up/down.
            Q(type=CI_RELATION_TYPES.REQUIRES.id) &
            Q(Q(child=self.root_ci))
        )

        ci_requires = CIRelation.objects.filter(
            # get children and parent one level up/down.
            Q(type=CI_RELATION_TYPES.REQUIRES.id) &
            Q(Q(parent=self.root_ci))
        )

        ci_is_role = CIRelation.objects.filter(
            Q(
                # get roles
                Q(type=CI_RELATION_TYPES.HASROLE.id) &
                Q(child=self.root_ci)
            )
        )

        ci_has_role = CIRelation.objects.filter(
            Q(
                Q(type=CI_RELATION_TYPES.HASROLE.id) &
                Q(parent=self.root_ci)
            )
        )

        ci_service = CIRelation.objects.filter(
            Q(
                # get venture node belongs to, and service venture belongs to.
                Q(type=CI_RELATION_TYPES.CONTAINS.id) &
                Q(
                    child__child=self.root_ci,
                    parent__type=CI_TYPES.SERVICE.id,
                    child__type=CI_TYPES.VENTURE.id,
                )
            )
        )
        self.graph = pygraph.classes.graph.graph()
        self.graph.add_nodes((c['pk'] for c in CI.objects.all().values('pk')))
        for relation in chain(
            ci_contained,
            ci_parented,
            ci_is_required,
            ci_requires,
            ci_is_role,
            ci_has_role,
            ci_service):
            if isinstance(relation, dict):
                parent = relation['parent']
                child = relation['child']
                type_ = relation['type']
            else:
                type_ = relation.type
                if relation.type == CI_RELATION_TYPES.CONTAINS.id:
                    # the only relation which we can traverse going straight
                    parent = relation.parent_id
                    child = relation.child_id
                else:
                    # opposite direction for graph traversal.
                    parent = relation.child_id
                    child = relation.parent_id
            try:
                self.graph.add_edge((parent, child), attrs=(type_,))
            except AdditionError:
                # ignore duplicated relations(types) in graph
                pass


