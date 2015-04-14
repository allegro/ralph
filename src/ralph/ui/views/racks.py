# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import collections

from bob.menu import MenuItem
from django.conf import settings
from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponseForbidden, HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext_lazy as _
from django.views.generic import CreateView

from ralph.account.models import Perm
from ralph.discovery.models import ReadOnlyDevice, Device, DeviceType
from ralph.ui.forms.devices import DeviceCreateForm
from ralph.ui.views.common import (
    Addresses,
    Asset,
    Base,
    BaseMixin,
    Components,
    History,
    Info,
    Scan,
    Software,
    TEMPLATE_MENU_ITEMS,
)
from ralph.ui.views.devices import BaseDeviceList
from ralph.ui.views.reports import ReportDeviceList
from ralph.util import presentation
from ralph_assets.models_assets import DeprecatedRalphRack
from ralph_assets.models_dc_assets import DataCenter


class BaseRacksMixin(object):
    submodule_name = 'racks'

    def set_rack(self):
        rack_identifier = self.kwargs.get('rack')
        if rack_identifier is None:
            self.rack = None
            return
        if (rack_identifier and rack_identifier != 'rack none' and
                rack_identifier != '-'):
            if rack_identifier.startswith('sn-'):
                rack_identifier = rack_identifier[3:].replace('-', ' ')
                self.rack = get_object_or_404(
                    Device,
                    sn=rack_identifier,
                    model__type__in=(
                        DeviceType.rack,
                        DeviceType.data_center,
                    )
                )
            else:
                if not rack_identifier.isdigit():
                    raise Http404()
                self.rack = get_object_or_404(
                    Device,
                    id=rack_identifier,
                    model__type__in=(
                        DeviceType.rack,
                        DeviceType.data_center,
                    )
                )
        else:
            self.rack = ''


def _slug(sn):
    return sn.replace(' ', '-').lower()


def _get_identifier(asset):
    if not asset:
        return asset
    return 'sn-%s' % _slug(asset.sn) if asset.sn else asset.id


class SidebarRacks(BaseRacksMixin):
    section = 'racks'

    def __init__(self, *args, **kwargs):
        super(SidebarRacks, self).__init__(*args, **kwargs)
        self.rack = None

    def get_context_data(self, **kwargs):
        self.set_rack()
        ret = super(SidebarRacks, self).get_context_data(**kwargs)
        icon = presentation.get_device_icon
        sidebar_items = [
            MenuItem(
                _("Unknown"),
                name='',
                fugue_icon='fugue-prohibition',
                view_name='racks',
                view_args=['-', ret['details'], '']
            )
        ]
        for dc in Device.objects.filter(
                model__type=DeviceType.data_center.id).order_by('name'):
            subitems = []
            sidebar_items.append(
                MenuItem(
                    dc.name,
                    name=_get_identifier(dc),
                    fugue_icon=icon(dc),
                    view_name='data_center_view',
                    subitems=subitems,
                    indent=' ',
                    view_args=[
                        _slug(dc.name),
                    ],
                    collapsible=True,
                    collapsed=not (
                        self.rack and (
                            self.rack == dc or self.rack.parent == dc
                        )
                    )
                )
            )
            for r in Device.objects.filter(
                model__type=DeviceType.rack.id
            ).filter(
                parent=dc
            ).order_by('name'):
                subitems.append(
                    MenuItem(
                        r.name,
                        name=_get_identifier(r),
                        indent=' ',
                        fugue_icon=icon(r),
                        view_name='racks',
                        view_args=[
                            _get_identifier(r), ret['details'], ''
                        ]
                    )
                )
        ret.update({
            'sidebar_items': sidebar_items,
            'sidebar_selected': _get_identifier(self.rack),
            'section': 'racks',
            'subsection': _get_identifier(self.rack),
            'show_bulk': True if self.rack else False,
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


class RacksSoftware(Racks, Software):
    pass


class RacksHistory(Racks, History):
    pass


class RacksAsset(Racks, Asset):
    pass


class RacksScan(Racks, Scan):
    submodule_name = 'racks'


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
                def key(x):
                    return (x.get_position() or '').rjust(100)
                c.sort(key=key, reverse=not sort.startswith('-'))
            elif sort == '':
                def key(x):
                    return (
                        x.model.type if x.model else None,
                        (x.get_position() or '').rjust(100)
                    )
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
        return queryset

    def paginate_queryset(self, queryset, page_size):
        if (self.rack and self.rack.model and
                self.rack.model.type == DeviceType.rack.id):
            queryset = list(self.sort_tree(queryset, self.sort))
        return super(RacksDeviceList, self).paginate_queryset(queryset,
                                                              page_size)

    def get_context_data(self, **kwargs):
        ret = super(RacksDeviceList, self).get_context_data(**kwargs)
        profile = self.request.user.get_profile()
        has_perm = profile.has_perm
        tab_items = ret['tab_items']
        if ret['subsection']:
            tab_items.append(
                MenuItem(
                    'Rack',
                    fugue_icon='fugue-media-player-phone',
                    href='../rack/?%s' % self.request.GET.urlencode()
                )
            )
        if has_perm(Perm.create_device, self.rack.venture if
                    self.rack else None):
            tab_items.append(
                MenuItem(
                    'Deploy',
                    fugue_icon='fugue-wand-hat',
                    name='add_device',
                    href='../add_device/?%s' % (self.request.GET.urlencode())
                )
            )
        ret.update({
            'subsection': self.rack.name if self.rack else self.rack,
            'subsection_slug': _get_identifier(self.rack),
        })
        return ret


class RacksRack(Racks, Base):
    template_name = 'ui/racks_rack.html'

    def dispatch(self, request, *args, **kwargs):
        self.new_rack = None
        response = super(RacksRack, self).dispatch(request, *args, **kwargs)
        try:
            old_rack = DeprecatedRalphRack.objects.get(id=self.rack.id)
        except DeprecatedRalphRack.DoesNotExist:
            pass
        else:
            for rack in old_rack.deprecated_asset_rack.all():
                self.new_rack = rack
        # NOTE: set_cookie method required value as a str not unicode
        response.set_cookie(str('rack_id'), self.new_rack and self.new_rack.id)
        return response

    def get_context_data(self, **kwargs):
        context = super(RacksRack, self).get_context_data(**kwargs)
        tab_items = context['tab_items']
        label = _('Rack view')
        if self.rack.model.type == DeviceType.data_center:
            label = _('Data center view')
        tab_items.insert(
            0,
            MenuItem(
                label,
                name='rack',
                fugue_icon='fugue-media-player-phone',
                href='../rack/?%s' % self.request.GET.urlencode()
            )
        )
        return context


class DeviceCreateView(BaseRacksMixin, CreateView):
    model = Device
    slug_field = 'id'
    slig_url_kwarg = 'device'

    def get_success_url(self):
        return self.request.path

    def get_template_names(self):
        return [self.template_name]

    def form_valid(self, form):
        self.set_rack()
        macs = [('', mac, 0) for mac in form.cleaned_data['macs'].split()]
        try:
            dc = self.rack.dc
        except AttributeError:
            dc = None
        try:
            rack = self.rack.rack
        except AttributeError:
            rack = None
        if self.rack == '':
            self.rack = None
        wed = form.cleaned_data['warranty_expiration_date']
        sed = form.cleaned_data['support_expiration_date']
        if form.cleaned_data['support_kind'] == '':
            form.cleaned_data['support_kind'] = None
        if form.cleaned_data['position'] == '':
            form.cleaned_data['position'] = None

        dev = Device.create(
            ethernets=macs,
            barcode=form.cleaned_data['barcode'],
            remarks=form.cleaned_data['remarks'],
            sn=form.cleaned_data['sn'],
            model=form.cleaned_data['model'],
            venture=form.cleaned_data['venture'],
            purchase_date=form.cleaned_data['purchase_date'],
            priority=1,
            position=form.cleaned_data['position'],
            chassis_position=form.cleaned_data['chassis_position'],
            margin_kind=form.cleaned_data['margin_kind'],
            deprecation_kind=form.cleaned_data['deprecation_kind'],
            price=form.cleaned_data['price'],
            warranty_expiration_date=wed,
            support_expiration_date=sed,
            support_kind=form.cleaned_data['support_kind'],
            venture_role=form.cleaned_data['venture_role'],
            parent=self.rack,
            dc=dc,
            rack=rack,
            user=self.request.user,
        )
        dev.name = form.cleaned_data['name']
        dev.save(priority=1, user=self.request.user)
        if all((
            'ralph_assets' in settings.INSTALLED_APPS,
            'asset' in form.cleaned_data.keys(),
        )):
            from ralph_assets.api_ralph import assign_asset
            asset = form.cleaned_data['asset']
            if asset:
                assign_asset(dev.id, asset.id)
        messages.success(self.request, "Device created.")
        return HttpResponseRedirect(self.request.path + '../info/%d' % dev.id)

    def get(self, *args, **kwargs):
        self.set_rack()
        has_perm = self.request.user.get_profile().has_perm
        try:
            venture = self.rack.venture
        except AttributeError:
            venture = None
        if not has_perm(Perm.create_device, venture):
            return HttpResponseForbidden(
                _("You don't have permission to create devices here.")
            )
        return super(DeviceCreateView, self).get(*args, **kwargs)

    def post(self, *args, **kwargs):
        self.set_rack()
        has_perm = self.request.user.get_profile().has_perm
        try:
            venture = self.rack.venture
        except AttributeError:
            venture = None
        if not has_perm(Perm.create_device, venture):
            return HttpResponseForbidden(
                _("You don't have permission to create devices here.")
            )
        return super(DeviceCreateView, self).post(*args, **kwargs)


class RacksAddDevice(Racks, DeviceCreateView):
    template_name = 'ui/racks-add-device.html'
    form_class = DeviceCreateForm

    def get_context_data(self, **kwargs):
        ret = super(RacksAddDevice, self).get_context_data(**kwargs)
        tab_items = ret['tab_items']
        ret['template_menu_items'] = TEMPLATE_MENU_ITEMS
        ret['template_selected'] = 'device'
        if ret['subsection']:
            tab_items.append(
                MenuItem(
                    'Rack',
                    fugue_icon='fugue-media-player-phone',
                    href='../rack/?%s' % self.request.GET.urlencode()
                )
            )

        tab_items.append(
            MenuItem(
                'Deploy',
                name='add_device',
                fugue_icon='fugue-wand-hat',
                href='../add_device/?%s' % (self.request.GET.urlencode())
            )
        )
        return ret


class ReportRacksDeviceList(ReportDeviceList, RacksDeviceList):
    pass


class DataCenterView(Racks, Base):
    submodule_name = 'racks'
    template_name = 'ui/data_center_view.html'

    def dispatch(self, request, data_center, *args, **kwargs):
        self.data_center = get_object_or_404(
            Device, name=data_center
        )
        response = super(DataCenterView, self).dispatch(
            request, *args, **kwargs
        )
        asset_dc = get_object_or_404(
            DataCenter, deprecated_ralph_dc_id=self.data_center.id
        )
        response.set_cookie(str('data_center_id'), asset_dc.id)
        return response

    def get_context_data(self, **kwargs):
        context = super(DataCenterView, self).get_context_data(**kwargs)
        context['data_center'] = self.data_center
        context['subsection'] = self.data_center.name
        context['details'] = 'data_center_view'
        tab_items = context['tab_items']
        if context['subsection']:
            tab_items.insert(0, MenuItem(
                _('Data center view'),
                fugue_icon='fugue-media-player-phone',
                name='data_center_view',
                view_name='data_center_view',
                view_args=[
                    slugify(self.data_center.name)
                ]
            ))
        return context
