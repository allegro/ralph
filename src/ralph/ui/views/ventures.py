# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import re

from django.contrib import messages
from django.db import models as db
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404

from bob.menu import MenuItem

from ralph.account.models import Perm
from ralph.business.models import Venture, VentureRole
from ralph.discovery.models import Device, ReadOnlyDevice
from ralph.ui.forms import RolePropertyForm, VentureFilterForm
from ralph.ui.views.common import (
    Addresses,
    Asset,
    Base,
    BaseMixin,
    Components,
    History,
    Info,
    Software,
    Scan,
)
from ralph.ui.views.devices import BaseDeviceList
from ralph.ui.views.reports import ReportDeviceList
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
            if depth > 0:
                icon = 'fugue-store-medium'
            if depth > 1:
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
            indent=' ',
            collapsed=True,
            collapsible=True,
        )
        item.venture_id = v.id
        item.subitems = venture_tree_menu(
            v.child_set.all(), details, show_all)
        for subitem in item.subitems:
            subitem.parent = item
        items.append(item)
    return items


class SidebarVentures(object):
    submodule_name = 'ventures'

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
                subitems = getattr(item, 'subitems', None)
                if subitems is None:
                    subitems = []
                stack.extend(subitems)

        self.set_venture()
        tab_items = ret['tab_items']
        if has_perm(Perm.read_device_info_generic, self.venture if
                    self.venture and self.venture != '*' else None):
            tab_items.append(MenuItem('Roles', fugue_icon='fugue-mask',
                                      href='../roles/?%s' % self.request.GET.urlencode()))
        ret.update({
            'sidebar_items': sidebar_items,
            'sidebar_selected': (_normalize_venture(self.venture.symbol) if
                                 self.venture and self.venture != '*' else self.venture or '-'),
            'section': 'ventures',
            'subsection': (_normalize_venture(self.venture.symbol) if
                           self.venture and self.venture != '*' else self.venture),
            'searchform': VentureFilterForm(self.request.GET),
            'searchform_filter': True,
            'show_bulk': True if self.venture else False,
        })
        return ret


class Ventures(SidebarVentures, BaseMixin):
    submodule_name = 'ventures'


class VenturesInfo(Ventures, Info):
    pass


class VenturesComponents(Ventures, Components):
    pass


class VenturesSoftware(Ventures, Software):
    pass


class VenturesAddresses(Ventures, Addresses):
    pass


class VenturesHistory(Ventures, History):
    pass


class VenturesAsset(Ventures, Asset):
    pass


class VenturesScan(Ventures, Scan):
    submodule_name = 'ventures'


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
        self.set_venture()
        role_id = self.kwargs.get('role')
        if role_id:
            self.role = get_object_or_404(VentureRole, id=role_id)
        else:
            self.role = None
        if self.form is None:
            if self.role:
                self.form = RolePropertyForm(initial={'role': role_id})
            else:
                self.form = RolePropertyForm(
                    initial={'venture': self.venture.id})
        return super(VenturesRoles, self).get(*args, **kwargs)

    def get_context_data(self, **kwargs):
        ret = super(VenturesRoles, self).get_context_data(**kwargs)
        has_perm = self.request.user.get_profile().has_perm
        ret.update({
            'items': (self.venture.venturerole_set.all() if
                      self.venture and self.venture != '*' else []),
            'role': self.role,
            'venture': self.venture,
            'form': self.form,
            'editable': has_perm(Perm.edit_ventures_roles, self.venture if
                                 self.venture and self.venture != '*' else None),
        })
        return ret


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


def _venture_children(venture, children):
    children.append(venture)
    for child in venture.child_set.all():
        _venture_children(child, children)


class VenturesDeviceList(SidebarVentures, BaseMixin, BaseDeviceList):
    submodule_name = 'ventures'

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
                db.Q(
                    venture__parent__parent__parent__parent__parent=self.venture
                )
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


class ReportVenturesDeviceList(ReportDeviceList, VenturesDeviceList):
    pass
