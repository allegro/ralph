#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import datetime

from django.db import models as db
from django.db.models.sql.aggregates import Aggregate
from ralph.discovery.models import HistoryCost, Processor


class SpanSum(Aggregate):
    sql_function = "SUM"
    sql_template = ("%(function)s(GREATEST(0, "
                    "DATEDIFF(LEAST(end, DATE('%(end)s')),"
                    "GREATEST(start, DATE('%(start)s')))) * %(field)s)")
    default_alias = 'spansum'

    def __init__(self, lookup, **extra):
        self.lookup = lookup
        self.extra = extra

    def add_to_query(self, query, alias, col, source, is_summary):
        super(SpanSum, self).__init__(col, source, is_summary, **self.extra)
        query.aggregate_select[alias] = self


def get_total_cost(query, start, end):
    return query.aggregate(
            SpanSum(
                'daily_cost',
                start=start.strftime('%Y-%m-%d'),
                end=end.strftime('%Y-%m-%d'),
            ),
    )['spansum']


def get_total_count(query, start, end):
    devices = HistoryCost.filter_span(start, end, query).values_list('device')
    count = devices.distinct().count()
    today = datetime.date.today()
    count_now = query.filter(end__gte=today).values_list(
        'device').distinct().count()
    return count, count_now, devices


def get_total_cores(devices, start, end):
    dev_ids = {dev for dev, in devices}
    core_count = Processor.objects.filter(device__id__in=dev_ids).aggregate(
        db.Sum('cores'))['cores__sum']
    return core_count


def get_total_virtual_cores(devices, start, end):
    dev_ids = devices.filter(device__model__type=203)
    core_count = Processor.objects.filter(device__id__in=dev_ids).aggregate(
        db.Sum('cores'))['cores__sum']
    return core_count
