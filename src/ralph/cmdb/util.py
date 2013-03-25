#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.db.models import Q


def report_filters(cls, order, filters=None):
    q = Q()
    if filters:
        filters_list = filters.pop()
        for name, value in filters_list.items():
            q &= Q(**{name:value})
        return cls.objects.filter(q).order_by(order).all()
    return cls.objects.order_by(order).all()


def add_filter(request, ci=None):
    filters = []
    if ci:
        filters.append({'ci': ci})
    if request.get('ci'):
        ci_id = CI.objects.select_related('id').filter(
            name=request.get('ci')
        )
        filters.append({'ci_id': ci_id[0]})
    if request.get('assignee'):
        filters.append({'assignee': request.get('assignee')})
    if request.get('jira_id'):
        filters.append({'jira_id': request.get('jira_id')})
    if request.get('issue_type'):
        filters.append({'issue_type': request.get('issue_type')})
    if request.get('status'):
        filters.append({'status': request.get('status')})
    if request.get('start_update') and request.get('end_update'):
        filters.append(
            {'update_date__lte': request.get('start_update')}
        )
        filters.append(
            {'update_date__gte': request.get('end_update')}
        )
    if request.get('start_resolved') and request.get('end_resolved'):
        filters.append(
            {'resolvet_date_lte': request.get('start_resolved')}
        )
        filters.append(
            {'resolvet_date_gte': request.get('end_resolved')}
        )
    if request.get('start_planned_start') and request.get('end_planned_start'):
        filters.append(
            {'planned_start_date_lte': request.get('start_planned_start')}
        )
        filters.append(
            {'planned_start_date_gte': request.get('end_planned_start')}
        )
    if request.get('start_planned_end') and request.get('end_planned_end'):
        filters.append(
            {'planned_end_date_lte': request.get('start_planned_end')}
        )
        filters.append(
            {'planned_end_date_gte': request.get('start_planned_end')}
        )
    return filters
