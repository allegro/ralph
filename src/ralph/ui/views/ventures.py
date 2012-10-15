# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import re
import datetime
import calendar

from django.contrib import messages
from django.db import models as db
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.utils import simplejson as json

from bob.menu import MenuItem

from ralph.account.models import Perm
from ralph.business.models import Venture, VentureRole, VentureExtraCost
from ralph.discovery.models import (ReadOnlyDevice, DeviceType, DataCenter,
                                    Device, DeviceModelGroup, HistoryCost,
                                    SplunkUsage, ComponentModel)
from ralph.ui.forms import (RolePropertyForm, DateRangeForm,
                            VentureFilterForm)
from ralph.ui.views.common import (Info, Prices, Addresses, Costs, Purchase,
                                   Components, History, Discover, BaseMixin,
                                   Base, DeviceDetailView, CMDB)
from ralph.ui.views.devices import BaseDeviceList
from ralph.ui.views.reports import Reports, ReportDeviceList
from ralph.ui.reports import get_total_cost, get_total_count
from ralph.util import presentation


def _normalize_venture(symbol):
    """
    >>> _normalize_venture('węgielek,Ziew')
    u'w.gielek.ziew'
    """
    return re.sub(r'[^\w]', '.', symbol).lower()


def collect_ventures(parent, ventures, items, depth=0):
    for v in ventures.filter(parent=parent):
        symbol = _normalize_venture(v.symbol)
        indent = ' ' * depth
        icon = presentation.get_venture_icon(v)
        if icon == 'fugue-store':
            if depth>0:
                icon = 'fugue-store-medium'
            if depth>1:
                icon = 'fugue-store-small'
        items.append((icon, v.name, symbol, indent, v))
        collect_ventures(v, ventures, items, depth + 1)


def venture_tree_menu(ventures, details, show_all=False):
    items = []
    if not show_all:
        ventures = ventures.filter(show_in_ralph=True)
    for v in ventures.order_by('-is_infrastructure', 'name'):
        symbol = _normalize_venture(v.symbol)
        icon = presentation.get_venture_icon(v)
        item = MenuItem(
            v.name, name=symbol,
            fugue_icon=icon,
            view_name='ventures',
            view_args=[symbol, details, ''],
            indent = ' ',
            collapsed = True,
            collapsible = True,
        )
        item.venture_id = v.id
        item.subitems = venture_tree_menu(
                v.child_set.all(), details, show_all)
        for subitem in item.subitems:
            subitem.parent = item
        items.append(item)
    return items


class SidebarVentures(object):
    def __init__(self, *args, **kwargs):
        super(SidebarVentures, self).__init__(*args, **kwargs)
        self.venture = None

    def set_venture(self):
        if self.venture is not None:
            return
        venture_symbol = self.kwargs.get('venture')
        if venture_symbol in ('', '-'):
            self.venture = ''
        elif venture_symbol == '*':
            self.venture = '*'
        elif venture_symbol:
            self.venture = get_object_or_404(Venture,
                    symbol__iexact=venture_symbol)
        else:
            self.venture = None

    def get_context_data(self, **kwargs):
        ret = super(SidebarVentures, self).get_context_data(**kwargs)
        self.set_venture()
        details = ret['details']
        profile = self.request.user.get_profile()
        has_perm = profile.has_perm
        ventures = profile.perm_ventures(Perm.list_devices_generic)
        show_all = self.request.GET.get('show_all')
        ventures = ventures.order_by('-is_infrastructure', 'name')

        sidebar_items = [
            MenuItem(fugue_icon='fugue-prohibition', label="Unknown",
                     name='-', view_name='ventures',
                     view_args=['-', details, '']),
            MenuItem(fugue_icon='fugue-asterisk', label="All ventures",
                     name='*', view_name='ventures',
                     view_args=['*', details, ''])
        ]
        sidebar_items.extend(venture_tree_menu(
                ventures.filter(parent=None), details, show_all))
        if self.venture and self.venture != '*':
            stack = list(sidebar_items)
            while stack:
                item = stack.pop()
                if getattr(item, 'venture_id', None) == self.venture.id:
                    parent = getattr(item, 'parent', None)
                    while parent:
                        parent.kwargs['collapsed'] = False
                        parent = getattr(parent, 'parent', None)
                    break
                stack.extend(getattr(item, 'subitems', []))

        self.set_venture()
        tab_items = ret['tab_items']
        if has_perm(Perm.read_device_info_generic, self.venture if
                    self.venture and self.venture != '*' else None):
            tab_items.append(MenuItem('Roles', fugue_icon='fugue-mask',
                            href='../roles/?%s' % self.request.GET.urlencode()))
        if has_perm(Perm.list_devices_financial, self.venture if
                    self.venture and self.venture != '*' else None):
            tab_items.append(MenuItem('Venture', fugue_icon='fugue-store',
                            href='../venture/?%s' %
                            self.request.GET.urlencode()))
        ret.update({
            'sidebar_items': sidebar_items,
            'sidebar_selected': (_normalize_venture(self.venture.symbol) if
                self.venture and self.venture != '*' else self.venture or '-'),
            'section': 'ventures',
            'subsection': (_normalize_venture(self.venture.symbol) if
                self.venture and self.venture != '*' else self.venture),
            'searchform': VentureFilterForm(self.request.GET),
            'searchform_filter': True,
        })
        return ret


class Ventures(SidebarVentures, BaseMixin):
    pass


class VenturesInfo(Ventures, Info):
    pass


class VenturesComponents(Ventures, Components):
    pass


class VenturesPrices(Ventures, Prices):
    pass


class VenturesAddresses(Ventures, Addresses):
    pass


class VenturesCosts(Ventures, Costs):
    pass


class VenturesHistory(Ventures, History):
    pass


class VenturesPurchase(Ventures, Purchase):
    pass


class VenturesDiscover(Ventures, Discover):
    pass


class VenturesReports(Ventures, Reports):
    pass


class VenturesRoles(Ventures, Base):
    template_name = 'ui/ventures-roles.html'

    def __init__(self, *args, **kwargs):
        super(VenturesRoles, self).__init__(*args, **kwargs)
        self.form = None

    def post(self, *args, **kwargs):
        self.set_venture()
        has_perm = self.request.user.get_profile().has_perm
        if not has_perm(Perm.edit_ventures_roles, self.venture if
                        self.venture and self.venture != '*' else None):
            messages.error(self.request, "No permission to edit that role.")
        else:
            self.form = RolePropertyForm(self.request.POST)
            if self.form.is_valid():
                self.form.save()
                messages.success(self.request, "Property created.")
                return HttpResponseRedirect(self.request.path)
            else:
                messages.error(self.request, "Correct the errors.")
        return self.get(*args, **kwargs)

    def get(self, *args, **kwargs):
        role_id = self.kwargs.get('role')
        if role_id:
            self.role = get_object_or_404(VentureRole, id=role_id)
        else:
            self.role = None
        if self.form is None:
            self.form = RolePropertyForm(initial={'role': role_id})
        return super(VenturesRoles, self).get(*args, **kwargs)

    def get_context_data(self, **kwargs):
        ret = super(VenturesRoles, self).get_context_data(**kwargs)
        self.set_venture()
        has_perm = self.request.user.get_profile().has_perm
        ret.update({
            'items': (self.venture.venturerole_set.all() if
                      self.venture and self.venture != '*' else []),
            'role': self.role,
            'form': self.form,
            'editable': has_perm(Perm.edit_ventures_roles, self.venture if
                               self.venture and self.venture != '*' else None),
        })
        return ret


def _total_dict(name, query, start, end, url=None):
    cost = get_total_cost(query, start, end)
    count, count_now, devices = get_total_count(query, start, end)
    if not count:
        return None
    return {
        'name': name,
        'count': count,
        'cost': cost,
        'count_now': count_now,
        'url': url,
    }

def _get_search_url(venture, dc=None, type=(), model_group=None):
    if venture == '':
        venture_id = '-'
    elif venture == '*':
        venture_id = '*'
    elif venture is None:
        venture_id = ''
    else:
        venture_id = venture.id
    params = [
        ('role', venture_id),
    ]
    for t in type:
        params.append(('device_type', '%d' % t))
    if model_group:
        params.append(('device_group', '%d' % model_group))
    if dc:
        params.append(('position', dc.name))
    return '/ui/search/info/?%s' % '&'.join('%s=%s' % p for p in params)


def _get_summaries(query, start, end, overlap=True, venture=None):
    if overlap:
        yield _total_dict('Servers', query.filter(
            device__model__type__in=(DeviceType.rack_server.id,
                             DeviceType.blade_server.id,
                             DeviceType.virtual_server.id)), start, end,
            _get_search_url(venture, type=(201, 202, 203)))
    for dc in DataCenter.objects.all():
        yield _total_dict('  • Servers in %s' % dc.name, query.filter(
            device__model__type__in=(DeviceType.rack_server.id,
                             DeviceType.blade_server.id,
                             DeviceType.virtual_server.id)
            ).filter(device__dc__iexact=dc.name), start, end,
            _get_search_url(venture, dc=dc, type=(201, 202, 203))
            )
        if overlap:
            yield _total_dict(
                '    ∙ Rack servers in %s' % dc.name, query.filter(
                        device__model__type=DeviceType.rack_server.id,
                    ).filter(device__dc__iexact=dc.name), start, end,
                        _get_search_url(venture, dc=dc, type=(201,))
                    )
            for mg in DeviceModelGroup.objects.filter(
                    type=DeviceType.rack_server.id).order_by('name'):
                yield _total_dict(
                    '        %s in %s' % (mg, dc.name), query.filter(
                            device__model__group=mg,
                        ).filter(device__dc__iexact=dc.name), start, end,
                        _get_search_url(venture, dc=dc, type=(201,),
                                        model_group=mg.id)
                        )
            yield _total_dict(
                '    ∙ Blade servers in %s' % dc.name, query.filter(
                        device__model__type=DeviceType.blade_server.id,
                    ).filter(device__dc__iexact=dc.name), start, end,
                        _get_search_url(venture, dc=dc, type=(202,))
                    )
            for mg in DeviceModelGroup.objects.filter(
                    type=DeviceType.blade_server.id).order_by('name'):
                yield _total_dict(
                    '        %s in %s' % (mg, dc.name), query.filter(
                            device__model__group=mg,
                        ).filter(device__dc__iexact=dc.name), start, end,
                            _get_search_url(venture, dc=dc, type=(202,),
                                            model_group=mg.id)
                        )
            yield _total_dict(
                '    ∙ Virtual servers in %s' % dc.name, query.filter(
                        device__model__type=DeviceType.virtual_server.id,
                    ).filter(device__dc__iexact=dc.name), start, end,
                        _get_search_url(venture, dc=dc, type=(203,))
                    )
    if overlap:
        yield _total_dict('Loadbalancers', query.filter(
                device__model__type__in=(DeviceType.load_balancer.id,)
            ), start, end, _get_search_url(venture, type=(103,)))
    for dc in DataCenter.objects.all():
        yield _total_dict(' • Loadbalancers in %s' % dc.name, query.filter(
                device__model__type__in=(DeviceType.load_balancer.id,)
            ).filter(device__dc__iexact=dc.name), start, end,
                _get_search_url(venture, dc=dc, type=(103,))
            )
    if overlap:
        yield _total_dict('Storage', query.filter(
            device__model__type__in=(
                DeviceType.storage.id,
                DeviceType.fibre_channel_switch.id,
            )), start, end,
                _get_search_url(venture, type=(301,))
            )
    for dc in DataCenter.objects.all():
        yield _total_dict(' • Storage in %s' % dc.name, query.filter(
            device__model__type__in=(
                    DeviceType.storage.id,
                    DeviceType.fibre_channel_switch.id,
                )
            ).filter(device__dc__iexact=dc.name), start, end,
                _get_search_url(venture, dc=dc, type=(301,))
            )
    if overlap:
        yield _total_dict('Network', query.filter(
            device__model__type__in=(
                DeviceType.switch.id,
                DeviceType.router.id,
                DeviceType.firewall.id,
                DeviceType.smtp_gateway.id,
                DeviceType.appliance.id,
            )
            ), start, end,
                _get_search_url(venture, type=(
                    DeviceType.switch.id,
                    DeviceType.router.id,
                    DeviceType.firewall.id,
                    DeviceType.smtp_gateway.id,
                    DeviceType.appliance.id,
                ))
            )
    for dc in DataCenter.objects.all():
        yield _total_dict(' • Network in %s' % dc.name, query.filter(
            device__model__type__in=(
                DeviceType.switch.id,
                DeviceType.router.id,
                DeviceType.firewall.id,
                DeviceType.smtp_gateway.id,
                DeviceType.appliance.id,
            )
            ).filter(device__dc__iexact=dc.name), start, end,
                _get_search_url(venture, dc=dc, type=(
                    DeviceType.switch.id,
                    DeviceType.router.id,
                    DeviceType.firewall.id,
                    DeviceType.smtp_gateway.id,
                    DeviceType.appliance.id,
                ))
            )
    yield _total_dict('Cloud', query.filter(
            device__model__type__in=(DeviceType.cloud_server.id,)
        ), start, end,
            _get_search_url(venture, type=(DeviceType.cloud_server.id,))
        )
    if overlap:
        yield _total_dict('Unknown', query.filter(
            device__model__type__in=(DeviceType.unknown.id,)), start, end,
                _get_search_url(venture, type=(DeviceType.unknown.id,))
            )
    for dc in DataCenter.objects.all():
        yield _total_dict(' • Unknown in %s' % dc.name, query.filter(
            device__model__type__in=(DeviceType.unknown.id,)
            ).filter(device__dc__iexact=dc.name), start, end,
                _get_search_url(venture, dc=dc, type=(DeviceType.unknown.id,))
            )
    splunk_usage = SplunkUsage.objects.filter(day__gte=start, day__lte=end)
    if venture and venture != '*':
        splunk_usage = splunk_usage.filter(db.Q(device__venture=venture) |
            db.Q(device__venture__parent=venture) |
            db.Q(device__venture__parent__parent=venture) |
            db.Q(device__venture__parent__parent__parent=venture) |
            db.Q(device__venture__parent__parent__parent__parent=venture))
    elif not venture: # specifically "devices with no venture set"
        splunk_usage = splunk_usage.filter(device__venture=None)
    if splunk_usage.count():
        splunk_size = splunk_usage.aggregate(db.Sum('size'))['size__sum'] or 0
        splunk_count = splunk_usage.values('device').distinct().count()
        yesterday = datetime.date.today() - datetime.timedelta(days=1)
        splunk_count_now = SplunkUsage.objects.filter(
                day=yesterday).values('device').distinct().count()
        url = None
        try:
            splunk_model = ComponentModel.objects.get(family='splunkvolume')
        except ComponentModel.DoesNotExist:
            pass
        else:
            if splunk_model.group_id:
                url = ('/ui/search/components/'
                       '?component_group=%d' % splunk_model.group_id)
        yield {
            'name': 'Splunk usage ({:,.0f} MB)'.format(
                                    splunk_size).replace(',', ' '),
            'cost': splunk_usage[0].get_price(size=splunk_size),
            'count': splunk_count,
            'count_now': splunk_count_now,
            'url': url,
        }
    for extra_id, in query.values_list('extra_id').distinct():
        if extra_id is None:
            continue
        extra = VentureExtraCost.objects.get(id=extra_id)
        q = query.filter(extra=extra)
        cost = get_total_cost(q, start, end)
        count, count_now, devices = get_total_count(q, start, end)
        yield {
            'name': extra.name + ' (from %s)' % extra.venture.name,
            'count': 'expires %s' % extra.expire.strftime(
                '%Y-%m-%d') if extra.expire else '',
            'cost': cost,
            'count_now': count_now,
        }
    if overlap:
        yield _total_dict('Total', query, start, end,
                _get_search_url(venture, type=()))


def _venture_children(venture, children):
    children.append(venture)
    for child in venture.child_set.all():
        _venture_children(child, children)


class VenturesVenture(SidebarVentures, Base):
    template_name = 'ui/ventures-venture.html'

    def get(self, *args, **kwargs):
        if 'start' in self.request.GET:
            self.form = DateRangeForm(self.request.GET)
            if not self.form.is_valid():
                messages.error(self.request, "Invalid date range")
        else:
            initial = {
                'start': datetime.date.today() - datetime.timedelta(days=30),
                'end': datetime.date.today(),
            }
            self.form = DateRangeForm(initial)
            self.form.is_valid()
        self.set_venture()
        has_perm = self.request.user.get_profile().has_perm
        if not has_perm(Perm.list_devices_financial, self.venture if
                        self.venture and self.venture != '*' else None):
            return HttpResponseForbidden(
                    "You don't have permission to see this.")
        return super(VenturesVenture, self).get(*args, **kwargs)

    def get_context_data(self, **kwargs):
        ret = super(VenturesVenture, self).get_context_data(**kwargs)
        start = None
        end = None
        if self.venture is None or not self.form.is_valid():
            items = []
            cost_data = []
            count_data = []
        else:
            if self.venture == '':
                query = HistoryCost.objects.filter(venture=None)
            elif self.venture == '*':
                query = HistoryCost.objects.exclude(venture=None)
            else:
                ventures = []
                _venture_children(self.venture, ventures)
                query = HistoryCost.objects.filter(
                    venture__in=ventures
                )
            start = self.form.cleaned_data['start']
            end = self.form.cleaned_data['end']
            query = HistoryCost.filter_span(start, end, query)
            items = _get_summaries(query.all(), start, end, True, self.venture)
            cost_data = []
            count_data = []
            one_day = datetime.timedelta(days=1)
            datapoints = set(dp for dp, in
                             query.values_list('start').distinct())
            datapoints |= set(dp for dp, in
                              query.values_list('end').distinct())
            datapoints |= set([start, end])
            datapoints = set(min(max(start, date or start), end) for
                             date in datapoints)
            for date in sorted(datapoints):
                timestamp = calendar.timegm(date.timetuple()) * 1000
                total_cost = get_total_cost(query, date, date + one_day)
                total_count, now_count, devices = get_total_count(
                        query, date, date + one_day)
                cost_data.append([timestamp, total_cost])
                count_data.append([timestamp, total_count])
        ret.update({
            'items': items,
            'venture': self.venture,
            'cost_data': json.dumps(cost_data),
            'count_data': json.dumps(count_data),
            'form': self.form,
            'start_date': start,
            'end_date': end,
        })
        return ret


class VenturesDeviceList(SidebarVentures, BaseMixin, BaseDeviceList):
    section = 'ventures'

    def user_allowed(self):
        self.set_venture()
        has_perm = self.request.user.get_profile().has_perm
        return has_perm(Perm.list_devices_generic, self.venture if
                        self.venture and self.venture != '*' else None)

    def get_queryset(self):
        if self.venture is None:
            queryset = ReadOnlyDevice.objects.none()
        elif self.venture == '*':
            queryset = Device.objects.all()
        elif self.venture == '':
            queryset = ReadOnlyDevice.objects.filter(
                    venture=None
                ).select_related(depth=3)
        else:
            queryset = ReadOnlyDevice.objects.filter(
                    db.Q(venture=self.venture) |
                    db.Q(venture__parent=self.venture) |
                    db.Q(venture__parent__parent=self.venture) |
                    db.Q(venture__parent__parent__parent=self.venture) |
                    db.Q(venture__parent__parent__parent__parent=self.venture) |
                    db.Q(venture__parent__parent__parent__parent__parent=
                         self.venture)
                ).select_related(depth=3)
        return self.sort_queryset(queryset)

    def get_context_data(self, **kwargs):
        ret = super(VenturesDeviceList, self).get_context_data(**kwargs)
        ret.update({
            'subsection': (self.venture.name if
                self.venture and self.venture != '*' else self.venture),
            'subsection_slug': (_normalize_venture(self.venture.symbol) if
                self.venture and self.venture != '*' else self.venture),
        })
        return ret


class VenturesCMDB(Ventures, CMDB, DeviceDetailView):
    pass


class ReportVenturesDeviceList(ReportDeviceList, VenturesDeviceList):
    pass
