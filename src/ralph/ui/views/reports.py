#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import datetime

from django.conf import settings
from django.contrib import messages
from django.core.cache import get_cache
from django.db import models as db
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.utils.safestring import mark_safe
from django.utils.html import escape
from django.utils.translation import ugettext_lazy as _

from bob.menu import MenuItem
from bob.csvutil import make_csv_response
from dj.choices import Choices
import django_rq

from ralph.account.models import Perm, ralph_permission
from ralph.business.models import Venture, VentureExtraCostType
from ralph.cmdb.models_ci import (
    CI,
    CIRelation,
    CI_STATE_TYPES,
    CI_RELATION_TYPES,
    CI_TYPES,
)
from ralph.deployment.models import DeploymentStatus
from ralph.discovery.models import (
    Device,
    DeviceType,
    MarginKind,
    SplunkUsage,
    HistoryCost,
)
from ralph.ui.forms import DateRangeForm, MarginsReportForm
from ralph.ui.reports import (
    get_total_cores,
    get_total_cost,
    get_total_count,
    get_total_virtual_cores,
)
from ralph.ui.views.common import Base, DeviceDetailView, _get_details
from ralph.ui.views.devices import DEVICE_SORT_COLUMNS
from ralph.ui.forms.reports import (
    DeprecationRangeReportForm,
    DevicesChoiceReportForm,
    SupportRangeReportForm,
    ReportVentureCost,
    ReportDeviceListForm,
    WarrantyRangeReportForm,
)
from ralph.util.async_reports import (
    get_cache_key,
    async_report_provider,
)
from ralph.util.presentation import get_device_icon, get_venture_icon


def threshold(days):
    return datetime.date.today() + datetime.timedelta(days=days)


def _get_after_report_invalidation_link(request, invalidate_param):
    get_params = request.GET.dict()
    del get_params[invalidate_param]
    return '%s?%s' % (
        request.path,
        '&'.join([
            '%s=%s' % (key, value)
            for key, value in get_params.items()
        ]),
    )


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
            MenuItem(
                "Device prices per venture",
                fugue_icon='fugue-computer',
                view_name='device_prices_per_venture'
            ),
        ]
        context.update({
            'sidebar_items': sidebar_items,
            'sidebar_selected': self.subsection,
            'section': 'reports',
            'subsection': self.subsection,
        })
        return context


class AsyncReportMixin(object):
    data_provider = None

    def get_data(self, *args, **kwargs):
        cache_key = get_cache_key(
            self.data_provider.func_name,
            *args,
            **kwargs
        )
        cache = get_cache(
            self.data_provider.async_report_cache_alias,
        )
        data = cache.get(cache_key)
        if data is not None:
            return None if data == 'in progress' else data
        cache.set(
            cache_key,
            'in progress',
            self.data_provider.async_report_results_expiration,
        )
        queue = django_rq.get_queue(
            name='reports' if 'reports' in settings.RQ_QUEUES else 'default',
        )
        queue.enqueue_call(
            func='%s.%s' % (
                self.data_provider.__module__,
                self.data_provider.func_name,
            ),
            args=args,
            kwargs=kwargs,
            timeout=3600,
            result_ttl=0,
        )

    def invalidate_data(self, *args, **kwargs):
        cache_key = get_cache_key(
            self.data_provider.func_name,
            *args,
            **kwargs
        )
        cache = get_cache(
            self.data_provider.async_report_cache_alias,
        )
        data = cache.get(cache_key)
        if data is None or data == 'in progress':
            return
        cache.delete(cache_key)


class ReportMargins(SidebarReports, Base):
    template_name = 'ui/report_margins.html'
    subsection = 'margins'
    perms = [
        {
            'perm': Perm.read_device_info_reports,
            'msg': _("You don't have permission to see reports."),
        },
    ]

    @ralph_permission(perms)
    def get(self, *args, **kwargs):
        self.margin_kinds = MarginKind.objects.all()
        if 'start' in self.request.GET:
            self.form = MarginsReportForm(self.margin_kinds, self.request.GET)
        else:
            self.form = MarginsReportForm(self.margin_kinds, initial={
                'start': datetime.date.today() - datetime.timedelta(days=30),
                'end': datetime.date.today(),
            })
        return super(ReportMargins, self).get(*args, **kwargs)

    @ralph_permission(perms)
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
                mk.sim_margin = self.form.get('m_%d' % mk.id) or 0
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


def _currency(value):
    return '{:,.2f} {}'.format(value or 0, settings.CURRENCY).replace(',', ' ')


def _report_ventures_get_totals(start, end, query, extra_types):
    venture_total = get_total_cost(query, start, end)
    venture_count, venture_count_now, devices = get_total_count(
        # Exclude all non-physical devices.
        query.exclude(
            device__model__type__in=(
                DeviceType.cloud_server,
                DeviceType.virtual_server,
                DeviceType.unknown,
                DeviceType.data_center,
                DeviceType.rack,
                DeviceType.management,
                DeviceType.switch_stack,
            ),
        ).exclude(
            device_id__isnull=True
        ),
        start,
        end,
    )
    venture_core_count = get_total_cores(devices, start, end)
    venture_virtual_core_count = get_total_virtual_cores(
        devices, start, end
    )
    q = query.filter(extra=None)
    venture_hardware_cost = get_total_cost(q, start, end)
    cloud_cost = get_total_cost(
        query.filter(
            device__model__type=DeviceType.cloud_server.id
        ), start, end
    )
    venture_extras = []
    for extra_type in extra_types:
        cost = None
        for extra_cost in extra_type.ventureextracost_set.all():
            q = query.filter(extra=extra_cost)
            c = get_total_cost(q, start, end)
            cost = cost + (c or 0) if cost else c
        venture_extras.append(cost)
    return {
        'count': venture_count,
        'count_now': venture_count_now,
        'core_count': venture_core_count,
        'virtual_core_count': venture_virtual_core_count,
        'hardware_cost': venture_hardware_cost,
        'cloud_cost': cloud_cost,
        'extras': venture_extras,
        'total': venture_total,
    }


@async_report_provider(timeout=3600, cache_alias='bigdata')
def _report_ventures_data_provider(start, end, ventures_ids, extra_types):
    ventures = Venture.objects.filter(id__in=ventures_ids).order_by('path')
    total_cloud_cost = get_total_cost(
        HistoryCost.objects.filter(
            device__model__type=DeviceType.cloud_server.id,
        ),
        start,
        end,
    )
    result = []
    for venture in ventures:
        query = HistoryCost.objects.filter(
            db.Q(venture=venture) |
            db.Q(venture__parent=venture) |
            db.Q(venture__parent__parent=venture) |
            db.Q(venture__parent__parent__parent=venture) |
            db.Q(venture__parent__parent__parent__parent=venture)
        ).exclude(device__deleted=True)
        data = _report_ventures_get_totals(start, end, query, extra_types)
        (
            splunk_cost,
            splunk_count,
            splunk_count_now,
            splunk_size,
        ) = SplunkUsage.get_cost(venture, start, end)
        data.update({
            'id': venture.id,
            'name': venture.name,
            'symbol': venture.symbol,
            'path': venture.path,
            'department': unicode(venture.department or ''),
            'margin': venture.get_margin(),
            'top_level': venture.parent is None,
            'venture_icon': get_venture_icon(venture),
            'cloud_use': (
                (data['cloud_cost'] or 0) / total_cloud_cost
            ) if total_cloud_cost else 0,
            'splunk_cost': splunk_cost,
        })
        result.append(data)
        if venture.parent is not None:
            continue
        if not venture.child_set.exists():
            continue
        query = HistoryCost.objects.filter(venture=venture)
        data = _report_ventures_get_totals(start, end, query, extra_types)
        (
            splunk_cost,
            splunk_count,
            splunk_count_now,
            splunk_size,
        ) = SplunkUsage.get_cost(venture, start, end, shallow=True)
        data.update({
            'id': venture.id,
            'name': '-',
            'symbol': venture.symbol,
            'path': venture.path,
            'department': unicode(venture.department or ''),
            'margin': venture.get_margin(),
            'top_level': False,
            'venture_icon': get_venture_icon(venture),
            'cloud_use': (
                (data['cloud_cost'] or 0) / total_cloud_cost
            ) if total_cloud_cost else 0,
            'splunk_cost': splunk_cost,
        })
        result.append(data)
    return result


class ReportVentures(SidebarReports, AsyncReportMixin, Base):
    template_name = 'ui/report_ventures.html'
    subsection = 'ventures'
    perms = [
        {
            'perm': Perm.read_device_info_reports,
            'msg': _("You don't have permission to see reports."),
        },
    ]
    data_provider = _report_ventures_data_provider

    def export_csv(self, venture_data, extra_types):
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
            'Cloud cost',
        ] + [extra_type.name for extra_type in extra_types] + [
            'Splunk cost',
            'Hardware cost',
            'Total cost',
        ]
        for data in venture_data:
            yield [
                '%d' % data['id'],
                data['name'],
                data['path'],
                data['department'],
                '%d%%' % data['margin'],
                '%d' % (data['count'] or 0),
                '%d' % (data['core_count'] or 0),
                '%d' % (data['virtual_core_count'] or 0),
                '%f' % (data['cloud_use'] or 0),
                _currency(data['cloud_cost']),
            ] + [_currency(v) for v in data['extras']] + [
                _currency(data['splunk_cost']),
                _currency(data['hardware_cost']),
                _currency(data['total']),
            ]

    @ralph_permission(perms)
    def get(self, *args, **kwargs):
        self.venture_data = []
        self.task_in_progress = False
        profile = self.request.user.get_profile()
        if 'start' in self.request.GET:
            self.form = DateRangeForm(self.request.GET)
        else:
            self.form = DateRangeForm(initial={
                'start': datetime.date.today() - datetime.timedelta(days=30),
                'end': datetime.date.today(),
            })
        self.extra_types = list(VentureExtraCostType.objects.annotate(
            cost_count=db.Count('ventureextracost')
        ).filter(cost_count__gt=0).order_by('name'))
        if self.form.is_valid():
            self.ventures = profile.perm_ventures(
                Perm.read_device_info_reports
            ).filter(
                db.Q(parent=None) | db.Q(parent__parent=None),
                show_in_ralph=True
            ).values_list(
                'id',
                flat=True,
            ).order_by('path')
            start = self.form.cleaned_data['start']
            end = self.form.cleaned_data['end']
            if self.request.GET.get('invalidate-cache') == 'true':
                self.invalidate_data(
                    start,
                    end,
                    self.ventures,
                    self.extra_types,
                )
                return HttpResponseRedirect(
                    _get_after_report_invalidation_link(
                        self.request,
                        'invalidate-cache',
                    ),
                )
            self.venture_data = self.get_data(
                start,
                end,
                self.ventures,
                self.extra_types,
            )
            if self.venture_data is None:
                self.task_in_progress = True
                messages.info(
                    self.request,
                    "Report processing in progress. Please wait...",
                )
        else:
            self.ventures = Venture.objects.none()
            self.venture_data = []
        if (
            self.request.GET.get('export') == 'csv' and
            self.venture_data is not None
        ):
            return make_csv_response(
                data=self.export_csv(self.venture_data, self.extra_types),
                filename='ReportVentures.csv',
            )
        return super(ReportVentures, self).get(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ReportVentures, self).get_context_data(**kwargs)
        context.update({
            'form': self.form,
            'ventures': self.ventures,
            'venture_data': self.venture_data,
            'profile': self.request.user.get_profile(),
            'extra_types': self.extra_types,
            'task_in_progress': self.task_in_progress,
        })
        return context


@async_report_provider(timeout=300)
def _report_services_data_provider():
    services = CI.objects.filter(type=CI_TYPES.SERVICE.id)
    relations = CIRelation.objects.filter(
        child__type=CI_TYPES.SERVICE.id,
        parent__type=CI_TYPES.VENTURE.id,
        type=CI_RELATION_TYPES.CONTAINS.id,
    )
    invalid_relations = []
    for relation in relations:
        child = relation.child
        child.state = CI_STATE_TYPES.NameFromID(child.state)
        child.venture_id = relation.parent.id
        child.venture = relation.parent.name
        child.relation_type = CI_RELATION_TYPES.NameFromID(relation.type)
        child.relation_type_id = relation.type
        invalid_relations.append(child)
    services_without_venture = []
    for service in services:
        if not CIRelation.objects.filter(
            parent=service,
            type=CI_RELATION_TYPES.CONTAINS,
            child__type=CI_TYPES.VENTURE
        ).exists():
            service.state = CI_STATE_TYPES.NameFromID(service.state)
            services_without_venture.append(service)
    return {
        'invalid_relations': invalid_relations,
        'services_without_venture': services_without_venture,
    }


class ReportServices(SidebarReports, AsyncReportMixin, Base):
    template_name = 'ui/report_services.html'
    subsection = 'services'
    perms = [
        {
            'perm': Perm.read_device_info_reports,
            'msg': _("You don't have permission to see reports."),
        },
    ]
    data_provider = _report_services_data_provider

    @ralph_permission(perms)
    def get(self, *args, **kwargs):
        self.data = self.get_data()
        if self.data is None:
            messages.info(
                self.request,
                "Report processing in progress. Please wait...",
            )
        return super(ReportServices, self).get(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ReportServices, self).get_context_data(**kwargs)
        context.update({
            'data': self.data,
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
    perms = [
        {
            'perm': Perm.read_device_info_reports,
            'msg': _("You don't have permission to see reports."),
        },
    ]

    def get_name(self, name, id):
        id = escape(id)
        name = escape(name)
        html = '<a href="/ui/search/info/%s">%s</a> (%s)' % (id, name, id)
        return mark_safe(html)

    @ralph_permission(perms)
    def get(self, *args, **kwargs):
        self.perm_edit = False

        request = self.request.GET
        csv_conf = {
            'name': 'report_devices',
            'url': None,
        }
        # Filtering of the cross
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
        no_par = self.request.GET.get('no_parent')
        rows = []
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
        if no_par:
            headers.append('No parent')
            queries.update({Q(parent=None) | Q(p_deleted=True)})
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
        # Filtering of the range
        # Support range
        s_start = self.request.GET.get('s_start', None)
        s_end = self.request.GET.get('s_end', None)
        if s_start and s_end:
            self.form_support_range = SupportRangeReportForm(request)
            if self.form_support_range.is_valid():
                headers = ('Name', 'Support expiration date')
                rows.extend([
                    (
                        self.get_name(dev.name, dev.id),
                        dev.support_expiration_date,
                    ) for dev in Device.objects.filter(
                        support_expiration_date__gte=s_start,
                        support_expiration_date__lte=s_end,
                    )
                ])
        else:
            self.form_support_range = SupportRangeReportForm(initial={
                's_start': datetime.date.today() - datetime.timedelta(days=30),
                's_end': datetime.date.today(),
            })
        # Deprecation range
        d_start = self.request.GET.get('d_start', None)
        d_end = self.request.GET.get('d_end', None)
        if d_start and d_end:
            self.form_deprecation_range = DeprecationRangeReportForm(request)
            if self.form_deprecation_range.is_valid():
                headers = ('Name', 'Depreciation date')
                rows.extend([
                    (
                        self.get_name(dev.name, dev.id),
                        dev.deprecation_date,
                    ) for dev in Device.objects.filter(
                        deprecation_date__gte=d_start,
                        deprecation_date__lte=d_end,
                    )
                ])
        else:
            self.form_deprecation_range = DeprecationRangeReportForm(initial={
                'd_start': datetime.date.today() - datetime.timedelta(days=30),
                'd_end': datetime.date.today(),
            })
        # Warranty range
        w_start = self.request.GET.get('w_start', None)
        w_end = self.request.GET.get('w_end', None)
        if w_start and w_end:
            self.form_warranty_range = WarrantyRangeReportForm(request)
            if self.form_warranty_range.is_valid():
                headers = ('Name', 'Warranty expiration date')
                rows.extend([
                    (
                        self.get_name(dev.name, dev.id),
                        dev.warranty_expiration_date,
                    ) for dev in Device.objects.filter(
                        warranty_expiration_date__gte=w_start,
                        warranty_expiration_date__lte=w_end,
                    )
                ])
        else:
            self.form_warranty_range = WarrantyRangeReportForm(initial={
                'w_start': datetime.date.today() - datetime.timedelta(days=30),
                'w_end': datetime.date.today(),
            })
        # Show devices active or / and deleted
        self.device_list = ReportDeviceListForm(request)
        all_devices = request.get('show_all_devices')
        all_deleted_devices = request.get('show_all_deleted_devices')
        if all_devices or all_deleted_devices:
            show_devices = None
            if all_devices and all_deleted_devices:
                show_devices = Device.admin_objects.all()
                csv_conf = {
                    'title': 'All devices (active and deleted)',
                    'name': 'report_all_devices',
                    'url': (
                        '?show_all_devices=on&'
                        'show_all_deleted_devices=on&export=csv'
                    ),
                }
            elif all_devices:
                show_devices = Device.objects.all()
                csv_conf = {
                    'title': 'All active devices',
                    'name': 'report_all_active_devices',
                    'url': '?show_all_devices=on&export=csv',
                }
            elif all_deleted_devices:
                show_devices = Device.admin_objects.filter(deleted=True)
                csv_conf = {
                    'title': 'All deleted devices',
                    'name': 'report_deleted_devices',
                    'url': '?show_all_deleted_devices=on&export=csv',
                }
            headers = [
                'Device', 'Model', 'SN', 'Barcode', 'Auto price', 'Venture',
                'Role', 'Remarks', 'Verified', 'Deleted',
            ]
            for dev in show_devices:
                rows.append([
                    dev.name,
                    dev.model,
                    dev.sn,
                    dev.barcode,
                    dev.cached_price,
                    dev.venture,
                    dev.role,
                    dev.remarks,
                    dev.verified,
                    dev.deleted,
                ])
        if request.get('export') == 'csv':
            rows.insert(0, headers)
            return make_csv_response(
                data=rows,
                filename=csv_conf.get('name'),
            )
        self.headers = headers
        self.rows = rows
        self.csv_url = csv_conf.get('url')
        self.title = csv_conf.get('title')
        return super(ReportDevices, self).get(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ReportDevices, self).get_context_data(**kwargs)
        context.update(
            {
                'title': self.title,
                'form_choice': self.form_choice,
                'form_support_range': self.form_support_range,
                'form_deprecation_range': self.form_deprecation_range,
                'form_warranty_range': self.form_warranty_range,
                'form_device_list': self.device_list,
                'csv_url': self.csv_url,
                'tabele_header': self.headers,
                'rows': self.rows,
                'perm_to_edit': self.perm_edit,
            }
        )
        return context


def _prices_per_venture_device_details(device, exclude=[]):
    components, stock = [], []
    total = 0
    for detail in _get_details(
        device,
        ignore_deprecation=True,
        exclude=exclude,
    ):
        model = detail.get('model')
        price = detail.get('price') or 0
        if not model:
            components.append({
                'model': 'n/a',
                'icon': 'n/a',
                'count': 'n/a',
                'price': 'n/a',
                'serial': 'n/a',
            })
        if model not in stock:
            components.append({
                'model': model.name if hasattr(model, 'name') else model,
                'icon': detail.get('icon'),
                'count': 1,
                'price': price,
                'serial': detail.get('serial'),
            })
        else:
            for component in components:
                if component['model'] == model:
                    component['count'] = component['count'] + 1
        total += price
        stock.append(model)
    venture = 'N/a'
    if device.venture and device.venture.symbol:
        venture = device.venture.symbol
    return {
        'device': {
            'id': device.id,
            'name': device.name,
            'sn': device.sn,
            'barcode': device.barcode,
            'deprecation_date': device.deprecation_date,
            'cached_price': device.cached_price,
            'icon': get_device_icon(device),
            'venture': venture,
            'role': device.role or 'N/a',
        },
        'components': components,
        'total': total,
        'deprecated': device.is_deprecated(),
    }


@async_report_provider(timeout=3600, cache_alias='bigdata')
def _prices_per_venture_data_provider(venture_id=None):
    if venture_id:
        try:
            venture = Venture.objects.get(id=venture_id)
        except Venture.DoesNotExist:
            return []
        devices_to_process = []
        for descendant in venture.find_descendant_ids():
            devices_to_process.extend(
                Device.objects.filter(venture_id=descendant),
            )
    else:
        devices_to_process = Device.objects.all()
    devices = []
    for device in devices_to_process:
        devices.append(
            _prices_per_venture_device_details(
                device=device,
                exclude=['software'],
            ),
        )
    return devices


class ReportDevicePricesPerVenture(SidebarReports, AsyncReportMixin, Base):
    template_name = 'ui/report_device_prices_per_venture.html'
    subsection = 'device_prices_per_venture'
    perms = [
        {
            'perm': Perm.read_device_info_reports,
            'msg': _("You don't have permission to see reports."),
        },
    ]
    data_provider = _prices_per_venture_data_provider

    def get_csv_data(self, devices):
        """Prepare data to export to CSV"""
        max_components_count, rows = 0, []
        for dev in devices:
            device = dev.get('device')
            components = dev.get('components')
            deprecated = dev.get('deprecated')
            row = [
                device['venture'],
                device['venture'],
                device['name'],
                device['role'],
                device['sn'] or 'N/a',
                device['barcode'] or 'N/a',
                device['cached_price'] if not deprecated else dev.get('total'),
                'True' if deprecated else 'False',
            ]
            max_components_count = max(max_components_count, len(components))
            for component in components:
                details = [
                    component['model'],
                    component['count'],
                    component['price'],
                ]
                row.extend(details)
            rows.append(row)
        headers = [
            'Venture', 'Venture ID', 'Device', 'Role', 'SN', 'Barcode',
            'Quoted price (PLN)', 'Deprecated',
        ]
        for i in range(max_components_count):
            headers.extend(
                ['Component name', 'Component count', 'Component total'],
            )
        rows.insert(0, headers)
        return rows

    @ralph_permission(perms)
    def get(self, *args, **kwargs):
        self.devices = []
        self.venture_id = self.request.GET.get('venture')
        self.export_all = self.request.GET.get('export-all', '') == 'csv'
        self.task_in_progress = False
        self.form = ReportVentureCost(
            initial={'venture': self.venture_id},
        )
        if self.request.GET.get('invalidate-cache', '') == 'true':
            self.invalidate_data(venture_id=self.venture_id)
            return HttpResponseRedirect(
                _get_after_report_invalidation_link(
                    self.request,
                    'invalidate-cache',
                ),
            )
        if self.venture_id:
            try:
                venture = Venture.objects.get(id=self.venture_id)
            except Venture.DoesNotExist:
                venture = None
        if any((
            self.venture_id and venture,
            not self.venture_id and self.export_all,
        )):
            self.devices = self.get_data(venture_id=self.venture_id)
            if self.devices is None:
                self.task_in_progress = True
                messages.info(
                    self.request,
                    "Report processing in progress. Please wait...",
                )
            if all((
                not self.task_in_progress,
                self.request.GET.get('export') == 'csv'
            )):
                filename = 'report_devices_prices_per_venture-%s-%s.csv' % (
                    venture.symbol, datetime.date.today(),
                )
                return make_csv_response(
                    data=self.get_csv_data(self.devices),
                    filename=filename,
                )
            if not self.task_in_progress and self.export_all:
                filename = 'report_devices_prices_per_venture-all-%s.csv' % (
                    datetime.date.today()
                )
                return make_csv_response(
                    data=self.get_csv_data(self.devices),
                    filename=filename,
                )
        return super(ReportDevicePricesPerVenture, self).get(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ReportDevicePricesPerVenture, self).get_context_data(
            **kwargs
        )
        context.update({
            'form': self.form,
            'rows': self.devices,
            'venture': self.venture_id,
            'task_in_progress': self.task_in_progress,
        })
        return context
