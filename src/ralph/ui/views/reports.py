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
from django.db.models import Q
from django.utils.safestring import mark_safe
from django.utils.html import escape

from bob.menu import MenuItem
from dj.choices import Choices

from ralph.account.models import Perm
from ralph.business.models import Venture
from ralph.cmdb.models_ci import (
    CI, CIRelation, CI_STATE_TYPES, CI_RELATION_TYPES, CI_TYPES
)
from ralph.deployment.models import DeploymentStatus
from ralph.discovery.models_device import MarginKind, DeviceType, Device
from ralph.discovery.models_history import HistoryCost
from ralph.ui.forms import DateRangeForm, MarginsReportForm
from ralph.ui.reports import (
    get_total_cost, get_total_count, get_total_cores, get_total_virtual_cores
)
from ralph.ui.views.common import Base, DeviceDetailView
from ralph.ui.views.devices import DEVICE_SORT_COLUMNS
from ralph.ui.forms.reports import (
    SupportRangeReportForm, DeprecationRangeReportForm,
    WarrantyRangeReportForm, DevicesChoiceReportForm
)
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
        columns=['venture', 'position', 'barcode', 'cost', 'price', 'remarks'],
    )
    no_venture_role = _('No venture and role').extra(
        filter=lambda device_list: device_list.filter(
            venture_role=None),
        columns=[
            'venture', 'position', 'barcode', 'cost', 'lastseen', 'remarks'
        ],
    )
    deactivated_support = _('Deactivated support').extra(
        filter=lambda device_list: device_list.filter(
            support_expiration_date__lte=datetime.date.today()
        ),
        columns=['venture', 'model', 'position', 'barcode',
                 'serial_number', 'remarks', 'support'],
    )
    support_expires30 = _('Support expires in 30 days').extra(
        filter=lambda device_list: device_list.filter(
            support_expiration_date__lte=threshold(30)),
        columns=[
            'venture', 'model', 'position', 'barcode', 'serial_number',
            'remarks', 'support'
        ],
    )
    support_expires60 = _('Support expires in 60 days').extra(
        filter=lambda device_list: device_list.filter(
            support_expiration_date__lte=threshold(60)),
        columns=[
            'venture', 'model', 'position', 'barcode', 'serial_number',
            'remarks', 'support'
        ],
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
    deprecation_devices = _('Deprecation devices').extra(
        filter=lambda device_list: device_list.filter(
            deprecation_date__lte=datetime.date.today()
        ),
        columns=[
            'venture', 'purchase', 'deprecation', 'deprecation_date',
            'remarks', 'barcode'
        ]
    )
    deprecation_devices30 = _('Deprecation devices in 30').extra(
        filter=lambda device_list: device_list.filter(
            deprecation_date__lte=threshold(30)
        ).filter(
            deprecation_date__gte=datetime.date.today()
        ),
        columns=[
            'venture', 'purchase', 'deprecation', 'deprecation_date',
            'remarks', 'barcode'
        ]
    )
    deprecation_devices60 = _('Deprecation devices in 60').extra(
        filter=lambda device_list: device_list.filter(
            deprecation_date__lte=threshold(60)
        ).filter(
            deprecation_date__gte=datetime.date.today()
        ),
        columns=[
            'venture', 'purchase', 'deprecation', 'deprecation_date',
            'remarks', 'barcode'
        ]
    )
    deprecation_devices90 = _('Deprecation devices in 90').extra(
        filter=lambda device_list: device_list.filter(
            deprecation_date__lte=threshold(90)
        ).filter(
            deprecation_date__gte=datetime.date.today()
        ),
        columns=[
            'venture', 'purchase', 'deprecation', 'deprecation_date',
            'remarks', 'barcode'
        ]
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
            MenuItem(
                "Devices",
                fugue_icon='fugue-computer',
                view_name='reports_devices'
            ),
            MenuItem(
                "Margins",
                fugue_icon='fugue-piggy-bank',
                view_name='reports_margins'
            ),
            MenuItem(
                "Services",
                fugue_icon='fugue-disc-share',
                view_name='reports_services'
            ),
            MenuItem(
                "Ventures",
                fugue_icon='fugue-store',
                view_name='reports_ventures'
            ),
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
                "You don't have permission to see reports."
            )
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
                id=self.form.cleaned_data['margin_venture']
            )
            query = HistoryCost.objects.filter(
                db.Q(venture=venture) |
                db.Q(venture__parent=venture) |
                db.Q(venture__parent__parent=venture) |
                db.Q(venture__parent__parent__parent=venture) |
                db.Q(venture__parent__parent__parent__parent=venture)
            ).exclude(device__deleted=True)
            total_cost = 0
            total_sim = 0
            total_count = 0
            start = self.form.cleaned_data['start']
            end = self.form.cleaned_data['end']
            for mk in self.margin_kinds:
                q = query.filter(
                    db.Q(device__margin_kind=mk) |
                    db.Q(
                        db.Q(device__margin_kind=None) &
                        db.Q(
                            db.Q(device__venture__margin_kind=mk) |
                            db.Q(device__venture__margin_kind=None,
                                 device__venture__parent__margin_kind=mk) |
                            db.Q(device__venture__margin_kind=None,
                                 device__venture__parent__margin_kind=None,
                                 device__venture__parent__parent__margin_kind=mk) |
                            db.Q(
                                device__venture__margin_kind=None,
                                device__venture__parent__margin_kind=None,
                                device__venture__parent__parent__margin_kind=None,
                                device__venture__parent__parent__parent__margin_kind=mk
                            )
                        )
                    )
                )
                mk.total = get_total_cost(q, start, end)
                mk.count, mk.count_now, devices = get_total_count(
                    q, start, end
                )
                mk.sim_margin = self.form.get('m_%d' % mk.id, 0) or 0
                mk.sim_cost = (
                    (mk.total or 0) / (1 + mk.margin / 100) *
                    (1 + mk.sim_margin / 100)
                )
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
            'zip_margin_kinds_form': zip(
                [f for f in self.form if not f.label], self.margin_kinds
            ),
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
                "You don't have permission to see reports."
            )
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
            total_cloud_cost = get_total_cost(
                HistoryCost.objects.filter(
                    device__model__type=DeviceType.cloud_server.id
                ), start, end
            )
            for venture in self.ventures:
                query = HistoryCost.objects.filter(
                    db.Q(venture=venture) |
                    db.Q(venture__parent=venture) |
                    db.Q(venture__parent__parent=venture) |
                    db.Q(venture__parent__parent__parent=venture) |
                    db.Q(venture__parent__parent__parent__parent=venture)
                ).exclude(device__deleted=True)
                venture.total = get_total_cost(query, start, end)
                (venture.count, venture.count_now,
                 devices) = get_total_count(query, start, end)
                venture.core_count = get_total_cores(devices, start, end)
                venture.virtual_core_count = get_total_virtual_cores(
                    devices, start, end
                )
                cloud_cost = get_total_cost(
                    query.filter(
                        device__model__type=DeviceType.cloud_server.id
                    ), start, end
                )
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


class ReportServices(SidebarReports, Base):
    template_name = 'ui/report_services.html'
    subsection = 'services'

    def get(self, *args, **kwargs):
        profile = self.request.user.get_profile()
        has_perm = profile.has_perm
        if not has_perm(Perm.read_device_info_reports):
            return HttpResponseForbidden(
                "You don't have permission to see reports.")
        self.perm_edit = False
        if has_perm(Perm.edit_configuration_item_relations):
            self.perm_edit = True
        services = CI.objects.filter(type=CI_TYPES.SERVICE.id)
        relations = CIRelation.objects.filter(
            child__type=CI_TYPES.SERVICE.id,
            parent__type=CI_TYPES.VENTURE.id,
            type=CI_RELATION_TYPES.CONTAINS.id,
        )
        self.invalid_relation = []
        for relation in relations:
            child = relation.child
            child.state = CI_STATE_TYPES.NameFromID(child.state)
            child.venture_id = relation.parent.id
            child.venture = relation.parent.name
            child.relation_type = CI_RELATION_TYPES.NameFromID(relation.type)
            child.relation_type_id = relation.type
            self.invalid_relation.append(relation.child)

        self.serv_without_ven = []
        for service in services:
            if service not in self.invalid_relation:
                service.state = CI_STATE_TYPES.NameFromID(service.state)
                self.serv_without_ven.append(service)
        return super(ReportServices, self).get(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ReportServices, self).get_context_data(**kwargs)
        context.update(
            {
                'invalid_relation': self.invalid_relation,
                'serv_without_ven': self.serv_without_ven,
                'perm_to_edit': self.perm_edit,
            }
        )
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


class ReportDevices(SidebarReports, Base):
    template_name = 'ui/report_devices.html'
    subsection = 'devices'

    def get_name(self, name, id):
        id = escape(id)
        name = escape(name)
        html = '<a href="/ui/search/info/%s">%s</a> (%s)' % (id, name, id)
        return mark_safe(html)

    def get(self, *args, **kwargs):
        profile = self.request.user.get_profile()
        has_perm = profile.has_perm
        if not has_perm(Perm.read_device_info_reports):
            return HttpResponseForbidden(
                "You don't have permission to see reports.")
        self.perm_edit = False
        if has_perm(Perm.edit_device_info_financial):
            self.perm_edit = True
        request = self.request.GET
        # CheckboxInput
        self.form_choice = DevicesChoiceReportForm(request)
        queries = {Q()}
        headers = ['Name']
        dep = self.request.GET.get('deprecation')
        no_dep = self.request.GET.get('no_deprecation')
        no_mar = self.request.GET.get('no_margin')
        no_sup = self.request.GET.get('no_support')
        no_pur = self.request.GET.get('no_purchase')
        no_ven = self.request.GET.get('no_venture')
        no_rol = self.request.GET.get('no_role')
        if dep:
            headers.append('Depreciation date')
            queries.update({Q(deprecation_date__lte=datetime.date.today())})
        if no_dep:
            headers.append('No depreciation date')
            queries.update({Q(deprecation_date=None)})
        if no_mar:
            headers.append('No depreciation kind')
            queries.update({Q(deprecation_kind=None)})
        if no_sup:
            headers.append('No support')
            queries.update({Q(support_expiration_date=None)})
        if no_pur:
            headers.append('No purchase')
            queries.update({Q(purchase_date=None)})
        if no_ven:
            headers.append('No venture')
            queries.update({Q(venture=None)})
        if no_rol:
            headers.append('No venture role')
            queries.update({Q(venture_role=None)})
        rows = []
        if len(queries) > 1:
            devices = Device.objects.filter(*queries)
            for dev in devices:
                row = []
                row.append(self.get_name(dev.name, dev.id))
                if dep:
                    row.append(dev.deprecation_date)
                if no_dep:
                    row.append(dev.deprecation_date)
                if no_mar:
                    row.append(dev.deprecation_kind)
                if no_sup:
                    row.append(dev.support_expiration_date)
                if no_pur:
                    row.append(dev.purchase_date)
                if no_ven:
                    row.append(dev.venture)
                if no_rol:
                    row.append(dev.venture_role)
                rows.append(row)
            # Support Range
        s_start = self.request.GET.get('s_start', None)
        s_end = self.request.GET.get('s_end', None)
        if s_start and s_end:
            self.form_support_range = SupportRangeReportForm(request)
            devices = Device.objects.all()
            devs = devices.filter(
                support_expiration_date__gte=s_start,
                support_expiration_date__lte=s_end,
            )
            headers = ('Name', 'Support expiration date')
            for dev in devs:
                name=self.get_name(dev.name, dev.id)
                rows.append([name,dev.support_expiration_date])
        else:
            self.form_support_range = SupportRangeReportForm(initial={
                's_start': datetime.date.today() - datetime.timedelta(days=30),
                's_end': datetime.date.today(),
                })
            # Deprecation Range
        d_start = self.request.GET.get('d_start', None)
        d_end = self.request.GET.get('d_end', None)
        if d_start and d_end:
            self.form_deprecation_range = DeprecationRangeReportForm(request)
            devices = Device.objects.all()
            devs = devices.filter(
                deprecation_date__gte=d_start,
                deprecation_date__lte=d_end,
            )
            headers = ('Name', 'Depreciation date')
            for dev in devs:
                name=self.get_name(dev.name, dev.id)
                rows.append([name, dev.deprecation_date])
        else:
            self.form_deprecation_range = DeprecationRangeReportForm(initial={
                'd_start': datetime.date.today() - datetime.timedelta(days=30),
                'd_end': datetime.date.today(),
                })
            # warranty_expiration_date Range
        w_start = self.request.GET.get('w_start', None)
        w_end = self.request.GET.get('w_end', None)
        if w_start and w_end:
            self.form_warranty_range = WarrantyRangeReportForm(request)
            devices = Device.objects.all()
            devs = devices.filter(
                warranty_expiration_date__gte=w_start,
                warranty_expiration_date__lte=w_end,
            )
            headers = ('Name', 'Warranty expiration date')
            for dev in devs:
                name=self.get_name(dev.name, dev.id)
                rows.append([name, dev.warranty_expiration_date])
        else:
            self.form_warranty_range = WarrantyRangeReportForm(initial={
                'w_start': datetime.date.today() - datetime.timedelta(days=30),
                'w_end': datetime.date.today(),
                })
        self.headers = headers
        self.rows = rows
        return super(ReportDevices, self).get(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ReportDevices, self).get_context_data(**kwargs)
        context.update(
            {
                'form_choice': self.form_choice,
                'form_support_range': self.form_support_range,
                'form_deprecation_range': self.form_deprecation_range,
                'form_warranty_range': self.form_warranty_range,
                'tabele_header': self.headers,
                'rows': self.rows,
                'perm_to_edit': self.perm_edit,
                }
        )
        return context
