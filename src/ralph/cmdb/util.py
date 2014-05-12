#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from bob.data_table import DataTableColumn
from django.db.models import Q

from ralph.cmdb.models import CI


def report_filters(cls, order, filters=None):
    if filters is False:
        return cls.objects.none()
    return cls.objects.filter(filters).order_by(order).all()


def add_filter(request, **kwargs):
    """Creates filters that can be used by report_filters method based on
    GET params from request.

    :param request: django request object
    :param ci: the CI to search for (None for all CIs)
    :return: the filters in a form of a [(field, value)] list or False if
        nothing should be found
    """
    filters = Q()
    for k, v in kwargs.items():
        filters |= Q(**{k: v})
    if request.get('ci'):
        ci = CI.objects.select_related('id').filter(
            name=request.get('ci')
        )
        if ci:
            filters &= Q(ci=ci[0])
        else:   # CI not found
            return False
    for key in ['assignee', 'jira_id', 'issue_type', 'status']:
        if request.get(key):
            filters &= Q(**{key: request.get(key)})
    if request.get('start_update') and request.get('end_update'):
        filters &= Q(
            update_date__lte=request.get('start_update'),
            update_date__gte=request.get('end_update'),
        )
    if request.get('start_resolved') and request.get('end_resolved'):
        filters &= Q(
            resolvet_date__lte=request.get('start_update'),
            resolvet_date__gte=request.get('end_update'),
        )
    if request.get('start_planned_start') and request.get('end_planned_start'):
        filters &= Q(
            planned_start_date__lte=request.get('start_planned_start'),
            planned_start_date__gte=request.get('end_planned_start'),
        )
    if request.get('start_planned_end') and request.get('end_planned_end'):
        filters &= Q(
            planned_end_date__lte=request.get('start_planned_end'),
            planned_end_date__gte=request.get('end_planned_end'),
        )
    return filters


def table_colums():
    _ = DataTableColumn
    columns = [
        _(
            'Issue updated',
            field='update_date',
            sort_expression='update_date',
            bob_tag=True,
        ),
        _(
            'Type',
            field='issue_type',
            sort_expression='issue_type',
            bob_tag=True,

        ),
        _(
            'Status',
            field='resolvet_date',
            sort_expression='resolvet_date',
            bob_tag=True,
        ),
        _(
            'Ci',
            field='ci',
            sort_expression='ci',
            bob_tag=True,
        ),
        _(
            'Summary',
            field='summary',
            bob_tag=True,
        ),
        _(
            'Assignee',
            field='assignee',
            bob_tag=True,
        ),
        _(
            'Description',
            field='description',
            bob_tag=True,
        ),
        _(
            'Analysis',
            field='analysis',
            bob_tag=True,
        ),
        _(
            'Problems',
            field='problems',
            bob_tag=True,
        ),
        _(
            'Planed start',
            field='planned_start_date',
            sort_expression='planned_start_date',
            bob_tag=True,
        ),
        _(
            'Planed end',
            field='planned_end_date',
            sort_expression='planned_end_date',
            bob_tag=True,
        ),
    ]
    return columns


def breadth_first_search_ci(root, criterion, up=True):
    """Perform a breadth-first search on a CI and its parents/children.

    :param root: The start of search
    :param criterion: A callable that takes a CI and returns a value that
        should evaluate to True if the search if succesful
    :param up: If true, the search will move to parents. Otherwise - to
        children.
    :return: A tuple (CI, criterion(CI)) on success or (None, None) on failure
    """
    queue = [root]
    enqueued = {root}
    while queue:
        current = queue.pop(0)
        result = criterion(current)
        if result:
            return current, result
        if up:
            to_search = current.get_parents()
        else:
            to_search = current.get_children()
        for ci in to_search:
            if ci.id not in enqueued:
                queue.append(ci)
                enqueued.add(ci.id)
    return None, None
