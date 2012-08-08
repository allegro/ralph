# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import ipaddr
import re

from django.contrib import messages
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import HttpResponseRedirect
from powerdns.models import Record

from ralph.account.models import Perm
from ralph.discovery.models import ReadOnlyDevice, Device
from ralph.ui.forms import SearchForm
from ralph.ui.views.common import (BaseMixin, Info, Prices, Addresses, Costs,
                                   Purchase, Components, History, Discover)
from ralph.ui.views.devices import BaseDeviceList
from ralph.ui.views.reports import Reports, ReportDeviceList


def _search_fields_or(fields, values):
    q = Q()
    for value in values:
        value = value.strip()
        if not value:
            continue
        for field in fields:
            q |= Q(**{field: value})
    return q


def _search_fields_and(fields, values):
    q = Q()
    for value in values:
        value = value.strip()
        if not value:
            continue
        qq = Q()
        for field in fields:
            qq |= Q(**{field: value})
        q &= qq
    return q


class SidebarSearch(object):
    def __init__(self, *args, **kwargs):
        super(SidebarSearch, self).__init__(*args, **kwargs)
        self.searchform = None

    def set_searchform(self):
        if self.searchform:
            return
        self.searchform = SearchForm(self.request.GET)
        if not self.searchform.is_valid():
            messages.error(self.request, "Invalid search query.")

    def get_context_data(self, **kwargs):
        ret = super(SidebarSearch, self).get_context_data(**kwargs)
        self.set_searchform()
        ret.update({
            'section': 'home',
            'subsection': 'search',
            'searchform': self.searchform,
        })
        return ret


class Search(SidebarSearch, BaseMixin):
    pass


class SearchDeviceList(SidebarSearch, BaseMixin, BaseDeviceList):
    def __init__(self, *args, **kwargs):
        super(SearchDeviceList, self).__init__(*args, **kwargs)
        self.query = None

    def user_allowed(self):
        return True

    def get_queryset(self):
        if self.query is not None:
            return self.query
        self.query = ReadOnlyDevice.objects.none()
        self.set_searchform()
        if self.searchform.is_valid():
            data = self.searchform.cleaned_data
            if data['deleted']:
                self.query = Device.admin_objects.all()
            else:
                self.query = Device.objects.all()
            if data['name']:
                name = data['name'].strip()
                names = set(n.strip('.') for (n,) in Record.objects.filter(
                        type='CNAME'
                    ).filter(
                        name__icontains=name
                    ).values_list('content'))
                ips = set(ip.strip('.') for (ip,) in Record.objects.filter(
                        type='A'
                    ).filter(
                        Q(name__icontains=name) |
                        Q(name__in=names)
                    ).values_list('content'))
                q = (_search_fields_or([
                    'name',
                    'ipaddress__hostname__icontains',
                ], name.split(' ')) | Q(
                    ipaddress__address__in=ips,
                ))
                self.query = self.query.filter(q).distinct()
            if data['address']:
                if '/' in data['address']:
                    net = ipaddr.IPNetwork(data['address'])
                    min_ip = int(net.network)
                    max_ip = int(net.broadcast)
                    self.query = self.query.filter(
                        ipaddress__number__gte=min_ip
                    ).filter(
                        ipaddress__number__lte=max_ip
                    )
                else:
                    q = _search_fields_or([
                        'ipaddress__address__icontains'
                    ], data['address'].split(' '))
                    self.query = self.query.filter(q).distinct()
            if data['remarks']:
                self.query = self.query.filter(
                        remarks__icontains=data['remarks']
                    )
            if data['model']:
                q = _search_fields_or([
                    'model__name__icontains',
                    'model__group__name__icontains',
                ], data['model'].split('|'))
                self.query = self.query.filter(q).distinct()
            if data['component']:
                q = _search_fields_or([
                    'genericcomponent__label__icontains',
                    'genericcomponent__model__name__icontains',
                    'genericcomponent__model__group__name__icontains',
                    'software__label__icontains',
                    'software__model__name__icontains',
                    'software__model__group__name__icontains',
                    'ethernet__mac__icontains',
                    'fibrechannel__label__icontains',
                    'fibrechannel__model__name__icontains',
                    'fibrechannel__model__group__name__icontains',
                    'storage__label__icontains',
                    'storage__model__name__icontains',
                    'storage__model__group__name__icontains',
                    'memory__label__icontains',
                    'memory__model__name__icontains',
                    'memory__model__group__name__icontains',
                    'processor__label__icontains',
                    'processor__model__name__icontains',
                    'processor__model__group__name__icontains',
                    'disksharemount__share__label__icontains',
                    'disksharemount__share__wwn__icontains',
                ], data['component'].split('|'))
                self.query = self.query.filter(q).distinct()
            if data['serial']:
                q = _search_fields_or([
                    'sn__icontains',
                    'ethernet__mac__icontains',
                    'genericcomponent__sn__icontains',
                ], data['serial'].split(' '))
                self.query = self.query.filter(q).distinct()
            if data['barcode']:
                self.query = self.query.filter(
                        barcode__icontains=data['barcode']
                    )
            if data['position']:
                q = Q()
                for part in data['position'].split(' '):
                    q |= _search_fields_and([
                        'position__icontains',
                        'dc__icontains',
                        'rack__icontains',
                    ], part.split('/'))
                self.query = self.query.filter(q).distinct()
            if data['history']:
                q = _search_fields_or([
                    'historychange__old_value__icontains',
                    'historychange__new_value__icontains',
                ], data['history'].split(' '))
                self.query = self.query.filter(q).distinct()
            if data['role']:
                q = Q()
                if data['role'].strip() == '-':
                    self.query = self.query.filter(venture=None)
                elif data['role'].strip() == '*':
                    self.query = self.query.exclude(venture=None)
                else:
                    for part in data['role'].split(' '):
                        try:
                            role_id = int(part)
                        except:
                            q |= _search_fields_and([
                                'venture_role__name__icontains',
                                'venture_role__parent__name__icontains',
                                'venture_role__parent__parent__name__icontains',
                                'venture__name__icontains',
                                'venture__symbol__icontains',
                            ], part.split('/'))
                        else:
                            q |= _search_fields_or([
                                'venture__id',
                                'venture__parent__id',
                                'venture__parent__parent__id',
                                'venture__parent__parent__parent__id',
                                'venture__parent__parent__parent__parent__id',
                            ], [str(role_id)])
                    self.query = self.query.filter(q).distinct()
            if data['device_group']:
                self.query = self.query.filter(
                        model__group_id=data['device_group']
                    )
            if data['component_group']:
                q = _search_fields_or([
                    'genericcomponent__model__group_id',
                    'software__model__group_id',
                    'fibrechannel__model__group_id',
                    'storage__model__group_id',
                    'memory__model__group_id',
                    'processor__model__group_id',
                    'disksharemount__share__model__group_id',
                ], [str(data['component_group'])])
                self.query = self.query.filter(q).distinct()
            if data['device_type']:
                self.query = self.query.filter(
                        model__type__in=data['device_type']
                    )
        profile = self.request.user.get_profile()
        if not profile.has_perm(Perm.read_dc_structure):
            self.query = profile.filter_by_perm(self.query,
                Perm.list_devices_generic)
        self.query = super(SearchDeviceList, self).get_queryset(self.query)
        return self.query

    def get(self, *args, **kwargs):
        details = self.kwargs.get('details')
        if details in (None, 'roles', 'venture'):
            search_url = reverse('search', args=['info', ''])
            url = '%s?%s' % (search_url, self.request.GET.urlencode())
            return HttpResponseRedirect(url)
        search_url = reverse('search', args=[details or 'info', ''])
        q = self.request.GET.get('q', '')
        if q:
            if re.match(r'^[\d./]+$', q):
                return HttpResponseRedirect('%s?address=%s' % (search_url, q))
            elif re.match(r'^[a-zA-Z.]+\s*/\s*[a-zA-Z.]+$', q):
                return HttpResponseRedirect('%s?role=%s' % (search_url, q))
            else:
                return HttpResponseRedirect('%s?name=%s' % (search_url, q))
        ret = super(SearchDeviceList, self).get(*args, **kwargs)
        query = self.get_queryset()
        if query.count() == 1:
            messages.info(self.request, "Found only one result.")
            url = '%s%d?%s' % (search_url, query[0].id,
                               self.request.GET.urlencode())
            return HttpResponseRedirect(url)
        return ret

    def get_context_data(self, **kwargs):
        ret = super(SearchDeviceList, self).get_context_data(**kwargs)
        ret.update({})
        return ret


class SearchInfo(Search, Info):
    pass


class SearchAddresses(Search, Addresses):
    pass


class SearchComponents(Search, Components):
    pass


class SearchPrices(Search, Prices):
    pass


class SearchCosts(Search, Costs):
    pass


class SearchHistory(Search, History):
    pass


class SearchPurchase(Search, Purchase):
    pass


class SearchDiscover(Search, Discover):
    pass


class SearchReports(Search, Reports):
    pass


class ReportSearchDeviceList(ReportDeviceList, SearchDeviceList):
    pass
