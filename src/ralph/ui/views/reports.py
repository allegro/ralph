#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import datetime

from bob.menu import MenuItem
from dj.choices import Choices

from ralph.deployment.models import DeploymentStatus
from ralph.ui.views.devices import DEVICE_SORT_COLUMNS


def threshold(days):
    return datetime.date.today() + datetime.timedelta(days=days)


class ReportType(Choices):
    _ = Choices.Choice

    no_ping1 = _('No ping since 1 day').extra(
        filter=lambda device_list: device_list.filter(
            ipaddress__last_seen__lte=threshold(-1)),
        columns=['venture', 'position', 'lastseen', 'remarks', 'lastping'],
    )
    no_ping3 = _('No ping since 3 days').extra(
        filter=lambda device_list: device_list.filter(
            ipaddress__last_seen__lte=threshold(-3)),
        columns=['venture', 'position', 'lastseen', 'remarks', 'lastping'],
    )
    no_ping7 = _('No ping since 7 days').extra(
        filter=lambda device_list: device_list.filter(
            ipaddress__last_seen__lte=threshold(-7)),
        columns=['venture', 'position', 'lastseen', 'remarks', 'lastping'],
    )
    no_venture_role = _('No venture and role').extra(
        filter=lambda device_list: device_list.filter(
            venture_role=None),
        columns=[
            'venture', 'position', 'barcode', 'cost', 'lastseen', 'remarks'
        ],
    )
    verified = _('Verified venture and role').extra(
        filter=lambda device_list: device_list.filter(verified=True),
        columns=['venture', 'remarks', 'barcode', 'serial_number']
    )
    deployment_open = _('Deployment open').extra(
        filter=lambda device_list: device_list.filter(
            deployment__status=DeploymentStatus.open
        ),
        columns=['venture', 'remarks', 'position', 'barcode'],
    )
    deployment_in_progress = _('Deployment in progress').extra(
        filter=lambda device_list: device_list.filter(
            deployment__status=DeploymentStatus.in_progress
        ),
        columns=['venture', 'remarks', 'position', 'barcode']
    )


class ReportDeviceList(object):
    template_name = 'ui/device_report_list.html'

    def get_report_type(self):
        try:
            return ReportType.from_name(self.kwargs['report'])
        except (KeyError, ValueError):
            return ReportType.no_ping1

    def get_context_data(self, **kwargs):
        result = super(ReportDeviceList, self).get_context_data(**kwargs)
        report_menu_items = (
            MenuItem(desc, href=name) for name, desc in
            ReportType(item=lambda v: (v.name, v.desc))
        )
        report_type = self.get_report_type()
        result.update({
            'report_menu_items': report_menu_items,
            'report_selected': report_type.desc.lower(),
            'columns': report_type.columns,
        })
        return result

    def get_queryset(self, queryset=None):
        if queryset is None:
            queryset = super(ReportDeviceList, self).get_queryset()
        queryset = self.get_report_type().filter(queryset).distinct()
        return self.sort_queryset(queryset, columns=DEVICE_SORT_COLUMNS)
