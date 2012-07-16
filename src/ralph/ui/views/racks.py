# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import collections

from django.shortcuts import get_object_or_404
from django.db.models import Q
from bob.menu import MenuItem

from ralph.discovery.models import ReadOnlyDevice, Device, DeviceType
from ralph.ui.views.common import (Info, Prices, Addresses, Costs,
    Purchase, Components, History, Discover)
from ralph.account.models import Perm
from ralph.util import presentation
from ralph.ui.views.common import BaseMixin
from ralph.ui.views.devices import BaseDeviceList
from ralph.ui.views.common import CMDB, DeviceDetailView


class SidebarRacks(object):
    def __init__(self, *args, **kwargs):
        super(SidebarRacks, self).__init__(*args, **kwargs)
        self.rack = None

    def set_rack(self):
        rack_name = self.kwargs.get('rack')
        if rack_name is None:
            self.rack = None
            return
        rack_name = rack_name.replace('-', ' ')
        if rack_name and rack_name != 'rack none':
            self.rack = get_object_or_404(
                    Device,
                    sn=rack_name,
                    model__type__in=(DeviceType.rack.id,
                                     DeviceType.data_center.id)
                )
        else:
            self.rack = ''

    def get_context_data(self, **kwargs):
        self.set_rack()
        ret = super(SidebarRacks, self).get_context_data(**kwargs)
        icon = presentation.get_device_icon
        def slug(sn):
            return sn.replace(' ', '-').lower()
        sidebar_items = [
            MenuItem("Unknown", name='', fugue_icon='fugue-prohibition',
                     view_name='racks', view_args=['', ret['details'], ''])
        ]
        for dc in Device.objects.filter(
                model__type=DeviceType.data_center.id).order_by('name'):
            sidebar_items.append(
                MenuItem(dc.name, name=slug(dc.sn), fugue_icon=icon(dc),
                         view_name='racks',
                         view_args=[slug(dc.sn), ret['details'], ''])
            )
            for r in Device.objects.filter(
                        model__type=DeviceType.rack.id
                    ).filter(
                        parent=dc
                    ).order_by('name'):
                sidebar_items.append(
                    MenuItem(r.name, name=slug(r.sn), indent=' ',
                         fugue_icon=icon(r),
                         view_name='racks',
                         view_args=[slug(r.sn), ret['details'], ''])
                )
        ret.update({
            'sidebar_items': sidebar_items,
            'sidebar_selected': slug(self.rack.sn) if self.rack else self.rack,
            'section': 'racks',
            'subsection': slug(self.rack.sn) if self.rack else self.rack,
        })
        return ret

class Racks(SidebarRacks, BaseMixin):
    pass

class RacksInfo(Racks, Info):
    pass

class RacksAddresses(Racks, Addresses):
    pass

class RacksComponents(Racks, Components):
    pass

class RacksCMDB(Racks, CMDB,DeviceDetailView ):
    pass

class RacksPrices(Racks, Prices):
    pass

class RacksCosts(Racks, Costs):
    pass

class RacksHistory(Racks, History):
    pass

class RacksPurchase(Racks, Purchase):
    pass

class RacksDiscover(Racks, Discover):
    pass

class RacksDeviceList(SidebarRacks, BaseMixin, BaseDeviceList):
    def user_allowed(self):
        has_perm = self.request.user.get_profile().has_perm
        return has_perm(Perm.read_dc_structure, None)

    def sort_tree(self, query, sort):
        children = collections.defaultdict(list)
        top = []
        for item in query:
            if item.model and item.model.type == DeviceType.rack.id:
                top.append((0, item))
            children[item.parent].append(item)
        while top:
            depth, item = top.pop()
            c = children[item]
            if sort in ('-position', 'position'):
                key = lambda x: x.get_position().rjust(100)
                c.sort(key=key, reverse=not sort.startswith('-'))
            elif sort == '':
                key = lambda x: (x.model.type if x.model else None,
                                 x.get_position().rjust(100))
                c.sort(key=key, reverse=True)
            top.extend((depth + 1, i) for i in c)
            item.depth = depth
            item.padding = '-' * depth
            yield item

    def get_queryset(self):
        self.set_rack()
        if self.rack is None:
            queryset = ReadOnlyDevice.objects.none()
        elif self.rack == '':
            queryset = ReadOnlyDevice.objects.filter(
                    parent=None
                ).select_related(depth=3)
        elif self.rack.model and self.rack.model.type != DeviceType.rack.id:
            queryset = Device.objects.filter(
                    Q(id=self.rack.id) |
                    Q(parent=self.rack)
                ).select_related(depth=3)
        else:
            queryset = Device.objects.filter(
                    Q(id=self.rack.id) |
                    Q(parent=self.rack) |
                    Q(parent__parent=self.rack) |
                    Q(parent__parent__parent=self.rack) |
                    Q(parent__parent__parent__parent=self.rack)
                ).select_related(depth=3)
        queryset = self.sort_queryset(queryset.order_by('model__type'))
        if self.rack and self.rack.model and self.rack.model.type == DeviceType.rack.id:
            queryset = list(self.sort_tree(queryset, self.sort))
        return queryset

    def get_context_data(self, **kwargs):
        ret = super(RacksDeviceList, self).get_context_data(**kwargs)
        ret.update({
            'subsection': self.rack.name if self.rack else self.rack,
            'subsection_slug': self.rack.sn if self.rack else self.rack,
        })
        return ret


