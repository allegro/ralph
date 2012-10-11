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
from ralph.discovery.models_device import MarginKind, DeviceType
from ralph.discovery.models_history import HistoryCost
from ralph.ui.reports import get_total_cost, get_total_count, get_total_cores, get_total_virtual_cores
from ralph.util import csvutil


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
    deactivated_support = _('Deactivated support').extra(
        filter=lambda device_list: device_list.filter(
            support_expiration_date__lte= datetime.date.today()),
        columns=['venture', 'model', 'position', 'barcode',
                 'serial_number', 'remarks', 'support'],
    )
    support_expires30 = _('Support expires in 30 days').extra(
            filter=lambda device_list: device_list.filter(
                support_expiration_date__lte=threshold(30)),
            columns=['venture', 'model', 'position', 'barcode',
                     'serial_number', 'remarks', 'support'],
            )
    support_expires60 = _('Support expires in 60 days').extra(
            filter=lambda device_list: device_list.filter(
                support_expiration_date__lte=threshold(60)),
            columns=['venture', 'model', 'position', 'barcode',
                     'serial_number', 'remarks', 'support'],
            )
    support_expires90 = _('Support expires in 90 days').extra(
            filter=lambda device_list: device_list.filter(
                support_expiration_date__lte=threshold(90)),
            columns=['venture', 'model', 'position', 'barcode',
                     'serial_number', 'remarks', 'support'],
            )
    verified = _('Verified venture and role').extra(
            filter=lambda device_list: device_list.filter(verified=True),
            columns=['venture', 'remarks', 'barcode', 'serial_number']
            )
    deployment_open = _('Deployment open').extra(
            filter=lambda device_list: device_list.filter(
                deployment__status=DeploymentStatus.open),
                columns=['venture', 'remarks', 'position', 'barcode']
            )
    deployment_in_progress = _('Deployment in progress').extra(
            filter=lambda device_list: device_list.filter(
                deployment__status=DeploymentStatus.in_progress),
                columns=['venture', 'remarks', 'position', 'barcode']
            )
    deployment_running = _('Deployment running').extra(
            filter=lambda device_list: device_list.filter(
                deployment__status=DeploymentStatus.in_deployment),
                columns=['venture', 'remarks', 'position', 'barcode']
            )
    deprecation_devices = _('Deprecation devices').extra(
            filter=lambda device_list: device_list.filter(
                deprecation_date__lte = datetime.date.today()),
                columns=['venture', 'purchase', 'deprecation',
                         'deprecation_date', 'remarks', 'barcode']
            )
    deprecation_devices30 = _('Deprecation devices in 30').extra(
            filter=lambda device_list: device_list.filter(
                deprecation_date__lte = threshold(30)).filter(
                    deprecation_date__gte=datetime.date.today()),
                columns=['venture', 'purchase', 'deprecation',
                         'deprecation_date','remarks', 'barcode']
            )
    deprecation_devices60 = _('Deprecation devices in 60').extra(
            filter=lambda device_list: device_list.filter(
                deprecation_date__lte = threshold(60)).filter(
                    deprecation_date__gte=datetime.date.today()),
                columns=['venture', 'purchase', 'deprecation',
                         'deprecation_date','remarks', 'barcode']
            )
    deprecation_devices90 = _('Deprecation devices in 90').extra(
            filter=lambda device_list: device_list.filter(
                    deprecation_date__lte = threshold(90)).filter(
                deprecation_date__gte=datetime.date.today()),
                columns=['venture', 'purchase', 'deprecation',
                         'deprecation_date', 'remarks', 'barcode']
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
        self.margin_kinds = MarginKind.objects.all()
        if 'start' in self.request.GET:
            self.form = MarginsReportForm(self.margin_kinds, self.request.GET)
        else:
            self.form = MarginsReportForm(self.margin_kinds, initial={
                'start': datetime.date.today() - datetime.timedelta(days=30),
                'end': datetime.date.today(),
            })
        return super(ReportMargins, self).get(*args, **kwargs)

    def post(self, *args, **kwargs):
        return self.get(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ReportMargins, self).get_context_data(**kwargs)
        if self.form.is_valid():
            venture = Venture.objects.get(
                    id=self.form.cleaned_data['margin_venture'])
            query = HistoryCost.objects.filter(
                db.Q(venture=venture) |
                db.Q(venture__parent=venture) |
                db.Q(venture__parent__parent=venture) |
                db.Q(venture__parent__parent__parent=venture) |
                db.Q(venture__parent__parent__parent__parent=venture)
            )
            total_cost = 0
            total_sim = 0
            total_count = 0
            start = self.form.cleaned_data['start']
            end = self.form.cleaned_data['end']
            for mk in self.margin_kinds:
                q = query.filter(db.Q(device__margin_kind=mk) |
                     db.Q(
                        db.Q(device__margin_kind=None) &
                        db.Q(
                            db.Q(device__venture__margin_kind=mk) |
                            db.Q(device__venture__margin_kind=None,
                                 device__venture__parent__margin_kind=mk) |
                            db.Q(device__venture__margin_kind=None,
                                 device__venture__parent__margin_kind=None,
                                 device__venture__parent__parent__margin_kind=mk) |
                            db.Q(device__venture__margin_kind=None,
                                 device__venture__parent__margin_kind=None,
                                 device__venture__parent__parent__margin_kind=None,
                        device__venture__parent__parent__parent__margin_kind=mk)
                        )
                    )
                )
                mk.total = get_total_cost(q, start, end)
                mk.count, mk.count_now, devices = get_total_count(q, start, end)
                mk.sim_margin = self.form.get('m_%d' % mk.id, 0) or 0
                mk.sim_cost = ((mk.total or 0) /
                               (1 + mk.margin/100) *
                               (1 + mk.sim_margin/100))
                total_sim += mk.sim_cost
                total_cost += mk.total or 0
                total_count += mk.count or 0
            context.update({
                'venture': venture,
                'total_cost': total_cost,
                'total_sim': total_sim,
                'total_count': total_count,
            })
        context.update({
            'form': self.form,
            'margin_kinds': self.margin_kinds,
            'zip_margin_kinds_form': zip([f for f in self.form if
                                          not f.label],
                                          self.margin_kinds),
        })
        return context


class ReportVentures(SidebarReports, Base):
    template_name = 'ui/report_ventures.html'
    subsection = 'ventures'

    def export_csv(self):
        def iter_rows():
            yield [
                'Venture ID',
                'Venture',
                'Path',
                'Department',
                'Default margin',
                'Device count',
                'Core count',
                'Virtual core count',
                'Cloud use',
                'Total cost'
            ]
            for venture in self.ventures:
                total = venture.total or 0
                yield [
                    '%d' % venture.id,
                    venture.name,
                    venture.path,
                    unicode(venture.department) if venture.department else '',
                    ('%d%%' % venture.margin_kind.margin
                        ) if venture.margin_kind else '',
                    '%d' % (venture.count or 0),
                    '%d' % (venture.core_count or 0),
                    '%d' % (venture.virtual_core_count or 0),
                    '%f' % (venture.cloud_use or 0),
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
            start = self.form.cleaned_data['start']
            end = self.form.cleaned_data['end']
            total_cloud_cost = get_total_cost(HistoryCost.objects.filter(
                    device__model__type=DeviceType.cloud_server.id
                ), start, end)
            for venture in self.ventures:
                query = HistoryCost.objects.filter(
                    db.Q(venture=venture) |
                    db.Q(venture__parent=venture) |
                    db.Q(venture__parent__parent=venture) |
                    db.Q(venture__parent__parent__parent=venture) |
                    db.Q(venture__parent__parent__parent__parent=venture)
                )
                venture.total = get_total_cost(query, start, end)
                (venture.count, venture.count_now,
                 devices) = get_total_count(query, start, end)
                venture.core_count = get_total_cores(devices, start, end)
                venture.virtual_core_count = get_total_virtual_cores(devices, start, end)
                cloud_cost = get_total_cost(query.filter(
                        device__model__type=DeviceType.cloud_server.id
                    ), start, end)
                venture.cloud_use = (cloud_cost or 0) / total_cloud_cost * 100
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
