#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import datetime
import cStringIO as StringIO

from django.db import models as db
from django.http import HttpResponseForbidden, HttpResponse
from django.conf import settings

from bob.menu import MenuItem
from dj.choices import Choices

from ralph.account.models import Perm
from ralph.deployment.models import DeploymentStatus
from ralph.ui.views.common import Base, DeviceDetailView
from ralph.ui.views.devices import DEVICE_SORT_COLUMNS
from ralph.ui.forms import DateRangeForm, MarginsReportForm
from ralph.business.models import Venture
from ralph.discovery.models_history import HistoryCost
from ralph.ui.reports import total_cost_count
from ralph.util import csvutil


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
            columns=['venture', 'remarks']
            )
    deployment_open = _('Deployment open').extra(
            filter=lambda device_list: device_list.filter(
                deployment__status=DeploymentStatus.open),
                columns=['venture', 'remarks']
            )
    deployment_in_progress = _('Deployment in progress').extra(
            filter=lambda device_list: device_list.filter(
                deployment__status=DeploymentStatus.in_progress),
                columns=['venture', 'remarks']
            )
    deployment_running = _('Deployment running').extra(
            filter=lambda device_list: device_list.filter(
                deployment__status=DeploymentStatus.in_deployment),
                columns=['venture', 'remarks']
            )


class Reports(DeviceDetailView):
    template_name = 'ui/device_reports.html'
    read_perm = Perm.read_device_info_history

    def get_context_data(self, **kwargs):
        result = super(Reports, self).get_context_data(**kwargs)
        return result

class SidebarReports(object):
    section = 'reports'
    subsection = ''

    def get_context_data(self, **kwargs):
        context = super(SidebarReports, self).get_context_data(**kwargs)
        sidebar_items = [
            MenuItem("Ventures", fugue_icon='fugue-store',
                     view_name='reports_ventures'),
            MenuItem("Margins", fugue_icon='fugue-piggy-bank',
                     view_name='reports_margins'),
        ]
        context.update({
            'sidebar_items': sidebar_items,
            'sidebar_selected': self.subsection,
            'section': 'reports',
            'subsection': self.subsection,
        })
        return context


class ReportMargins(SidebarReports, Base):
    template_name = 'ui/report_margins.html'
    subsection = 'margins'

    def get(self, *args, **kwargs):
        profile = self.request.user.get_profile()
        has_perm = profile.has_perm
        if not has_perm(Perm.read_device_info_reports):
            return HttpResponseForbidden(
                    "You don't have permission to see reports.")
        self.form = MarginsReportForm(self.request.GET)
        return super(ReportMargins, self).get(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ReportMargins, self).get_context_data(**kwargs)
        context.update({
            'form': self.form,
        })
        return context


class ReportVentures(SidebarReports, Base):
    template_name = 'ui/report_ventures.html'
    subsection = 'ventures'

    def export_csv(self):
        def iter_rows():
            yield [
                'Venture',
                'Path',
                'Department',
                'Default margin',
                'Total cost'
            ]
            for venture in self.ventures:
                total = venture.total or 0
                yield [
                    venture.name,
                    venture.path,
                    unicode(venture.department) if venture.department else '',
                    ('%d%%' % venture.margin_kind.margin
                        ) if venture.margin_kind else '',
                    '{:,.2f} {}'.format(total, settings.CURRENCY).replace(',', ' '),
                ]
        f = StringIO.StringIO()
        csvutil.UnicodeWriter(f).writerows(iter_rows())
        response = HttpResponse(f.getvalue(), content_type='application/csv')
        response['Content-Disposition'] = 'attachment; filename=ventures.csv'
        return response

    def get(self, *args, **kwargs):
        profile = self.request.user.get_profile()
        has_perm = profile.has_perm
        if not has_perm(Perm.read_device_info_reports):
            return HttpResponseForbidden(
                    "You don't have permission to see reports.")
        if 'start' in self.request.GET:
            self.form = DateRangeForm(self.request.GET)
        else:
            self.form = DateRangeForm(initial={
                'start': datetime.date.today() - datetime.timedelta(days=30),
                'end': datetime.date.today(),
            })
        if self.form.is_valid():
            self.ventures = profile.perm_ventures(
                    Perm.read_device_info_reports
                ).filter(
                    db.Q(parent=None) |
                    db.Q(parent__parent=None),
                    show_in_ralph=True
                ).order_by('path')
            for venture in self.ventures:
                (venture.total, venture.count,
                 venture.count_now) = total_cost_count(
                         HistoryCost.objects.filter(
                             db.Q(venture=venture) |
                             db.Q(venture__parent=venture) |
                             db.Q(venture__parent__parent=venture) |
                             db.Q(venture__parent__parent__parent=venture) |
                             db.Q(venture__parent__parent__parent__parent=venture)
                         ).distinct(),
                         self.form.cleaned_data['start'],
                         self.form.cleaned_data['end'],
                    )
        else:
            self.ventures = Venture.objects.none()
        if self.request.GET.get('export') == 'csv':
            return self.export_csv()
        return super(ReportVentures, self).get(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ReportVentures, self).get_context_data(**kwargs)
        context.update({
            'form': self.form,
            'ventures': self.ventures,
            'profile': self.request.user.get_profile(),
        })
        return context


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
