#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import datetime

from bob.menu import MenuItem
from dj.choices import Choices
from django.template.defaultfilters import slugify

from ralph.account.models import Perm
from ralph.ui.views.common import Base, DeviceDetailView
from ralph.ui.views.devices import DEVICE_SORT_COLUMNS


def threshold(days):
    return datetime.date.today() + datetime.timedelta(days=days)


class ReportType(Choices):
    _ = Choices.Choice

    no_ping1 = _('No ping since 1 day').extra(
            filter=lambda device_list: device_list.filter(
                ipaddress__last_seen__lte=threshold(-1)),
            columns=['venture', 'position', 'lastseen', 'remarks'],
            )
    no_ping3 = _('No ping since 3 days').extra(
            filter=lambda device_list: device_list.filter(
                ipaddress__last_seen__lte=threshold(-3)),
            columns=['venture', 'position', 'lastseen', 'remarks'],
            )
    no_ping7 = _('No ping since 7 days').extra(
            filter=lambda device_list: device_list.filter(
                ipaddress__last_seen__lte=threshold(-7)),
            columns=['venture', 'position', 'lastseen', 'remarks'],
            )
    no_purchase_date = _('No purchase date').extra(
            filter=lambda device_list: device_list.filter(
                purchase_date=None),
            columns=['venture', 'position', 'barcode', 'cost', 'price',
                'remarks'],
            )
    no_venture_role = _('No venture and role').extra(
            filter=lambda device_list: device_list.filter(
                venture_role=None),
            columns=['venture', 'position', 'barcode', 'cost', 'lastseen',
                'remarks'],
            )
    support_expires30 = _('Support expires in 30 days').extra(
            filter=lambda device_list: device_list.filter(
                support_expiration_date__lte=threshold(30)),
            columns=['venture', 'position', 'barcode', 'price', 'lastseen',
                'remarks'],
            )
    support_expires60 = _('Support expires in 60 days').extra(
            filter=lambda device_list: device_list.filter(
                support_expiration_date__lte=threshold(60)),
            columns=['venture', 'position', 'barcode', 'price', 'lastseen',
                'remarks'],
            )
    support_expires90 = _('Support expires in 90 days').extra(
            filter=lambda device_list: device_list.filter(
                support_expiration_date__lte=threshold(90)),
            columns=['venture', 'position', 'barcode', 'price', 'lastseen',
                'remarks'],
            )
    verified = _('Verified venture and role').extra(
            filter=lambda device_list: device_list.filter(verified=True),
            columns=['venture', 'remarks'])


class Reports(DeviceDetailView):
    template_name = 'ui/device_reports.html'
    read_perm = Perm.read_device_info_history

    def get_context_data(self, **kwargs):
        result = super(Reports, self).get_context_data(**kwargs)
        return result


class ReportList(Base):
    section = 'reports'
    template_name = 'ui/report_list.html'


class ReportDeviceList(object):
    template_name = 'ui/device_report_list.html'

    def get_report_type(self):
        try:
            return ReportType.from_name(self.kwargs['report'])
        except (KeyError, ValueError):
            return ReportType.no_ping1

    def get_context_data(self, **kwargs):
        result = super(ReportDeviceList, self).get_context_data(**kwargs)
        report_menu_items = (MenuItem(desc, href=name) for name, desc in
            ReportType(item=lambda v: (v.name, v.desc)))
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
