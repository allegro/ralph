#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import datetime

from django.db.models.sql.aggregates import Aggregate
from ralph.discovery.models import HistoryCost, DeviceType


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


class SpanCount(Aggregate):
    sql_function = "SUM"
    sql_template = ("%(function)s(GREATEST(0, "
                    "DATEDIFF(LEAST(end, DATE('%(end)s')),"
                    "GREATEST(start, DATE('%(start)s')))))")
    default_alias = 'spansum'

    def __init__(self, **extra):
        self.lookup = 'id'
        self.extra = extra

    def add_to_query(self, query, alias, col, source, is_summary):
        super(SpanCount, self).__init__(col, source, is_summary, **self.extra)
        query.aggregate_select[alias] = self


def get_total_cost(query, start, end):
    """
    Calculate a total cost of the HistoryCost query in the specified time span.
    """
    return query.aggregate(
        SpanSum(
            'daily_cost',
            start=start.strftime('%Y-%m-%d'),
            end=end.strftime('%Y-%m-%d'),
        ),
    )['spansum']


def get_total_count(query, start, end):
    """
    Count the devices in the given HistoryCost query in the specified time span.
    The devices that are not in the query for the whole time are counted as a
    fraction.
    Additionally, the function returns the count of devices at the current date
    time span, and a query with all the devices from the query.
    """
    days = (end - start).days or 1
    devices = HistoryCost.filter_span(start, end, query).values_list('device')
    today = datetime.date.today()
    count_now = query.filter(
        end__gte=today
    ).values_list(
        'device'
    ).distinct().count()
    count = float(query.aggregate(
        SpanCount(
            start=start.strftime('%Y-%m-%d'),
            end=end.strftime('%Y-%m-%d'),
        ),
    )['spansum'] or 0) / days
    return count, count_now, devices


def get_total_cores(query, start, end):
    """
    Calculate the number of cores in the given HistoryCost query. Devices that
    are not in the query for the whole time span are counted as a fraction.
    Only the physical servers are included.
    """
    days = (end - start).days or 1
    query = query.exclude(device__model__type=DeviceType.virtual_server.id)
    return float(query.aggregate(
        SpanSum(
            'cores',
            start=start.strftime('%Y-%m-%d'),
            end=end.strftime('%Y-%m-%d'),
        ),
    )['spansum'] or 0) / days


def get_total_virtual_cores(query, start, end):
    """
    Calculate the number of cores in the given HistoryCost query. Devices that
    are not in the query for the whole time span are counted as a fraction.
    Only the virtual servers are included.
    """
    days = (end - start).days or 1
    query = query.filter(device__model__type=DeviceType.virtual_server.id)
    return float(query.aggregate(
        SpanSum(
            'cores',
            start=start.strftime('%Y-%m-%d'),
            end=end.strftime('%Y-%m-%d'),
        ),
    )['spansum'] or 0) / days
