# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import decimal

from bob.menu import MenuItem, MenuHeader
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.conf import settings

from ralph.account.models import Perm
from ralph.discovery.models import (DeviceType, ComponentType, DeviceModel,
                                    DeviceModelGroup, ComponentModelGroup,
                                    ComponentModel, Storage, Memory, Processor,
                                    DiskShare, FibreChannel, GenericComponent,
                                    Software, OperatingSystem, Device)
from ralph.discovery.models_history import HistoryModelChange
from ralph.ui.forms import ComponentModelGroupForm, DeviceModelGroupForm
from ralph.ui.views.common import Base
from ralph.util import pricing
from ralph.util.presentation import COMPONENT_ICONS, DEVICE_ICONS


MODEL_GROUP_SORT_COLUMNS = {
    'name': ('name',),
    'size': ('chassis_size',),
}
HISTORY_SORT_COLUMNS = {
    'date': ('date',),
    'user': ('user__login',),
    'field_name': ('field_name',),
}
PAGE_SIZE = 25
MAX_PAGE_SIZE = 65535



def _prepare_query(request, query, tree=False, columns={}, default_sort=''):
    if query:
        query = query.select_related(depth=3)
    try:
        page = int(request.GET.get('page', 1))
    except ValueError:
        page = 1
    sort = request.GET.get('sort', default_sort)
    sort_columns = columns.get(sort.strip('-'), ())
    if sort.startswith('-'):
        sort_columns = ['-' + col for col in sort_columns]
    if query and sort:
        query = query.order_by(*sort_columns)
    return query, sort, page


def _prepare_model_groups(request, query, tree=False):
    query, sort, page = _prepare_query(request, query, tree,
            MODEL_GROUP_SORT_COLUMNS, default_sort='-count')
    for g in query:
        g.count = g.get_count()
    query = [g for g in query if g.count]
    if sort in ('count', '-count'):
        if sort.startswith('-'):
            query.sort(key=lambda g: -g.count)
        else:
            query.sort(key=lambda g: g.count)
    if page == 0:
        pages = Paginator(query, MAX_PAGE_SIZE)
        items = pages.page(1)
    else:
        pages = Paginator(query, PAGE_SIZE)
        items = pages.page(page)
    return {
        'sort': sort,
        'items': items,
    }


class Catalog(Base):
    section = 'catalog'
    template_name = 'ui/catalog.html'

    def get(self, *args, **kwargs):
        if not self.request.user.get_profile().has_perm(
                Perm.edit_device_info_financial):
            return HttpResponseForbidden('You have no permission to view catalog')
        return super(Catalog, self).get(*args, **kwargs)


    def get_context_data(self, **kwargs):
        ret = super(Catalog, self).get_context_data(**kwargs)
        try:
            model_type_id = int(self.kwargs.get('type', ''))
        except ValueError:
            model_type_id = None
        kind = self.kwargs.get('kind')
        sidebar_items = (
            [MenuHeader('Components')] +
            [MenuItem(
                    label=t.raw.title(),
                    name='component-%d' % t.id,
                    fugue_icon = COMPONENT_ICONS[t.id],
                    view_name='catalog',
                    view_args=('component', t.id),
                ) for t in ComponentType(item=lambda t: t)] +
            [MenuHeader('Devices')] +
            [MenuItem(
                        label=t.raw.title(),
                        name='device-%d' % t.id,
                        fugue_icon = DEVICE_ICONS[t.id],
                        view_name='catalog',
                        view_args=('device', t.id),
                    ) for t in DeviceType(item=lambda t: t)] +
            [MenuHeader('History'),
             MenuItem('History', fugue_icon='fugue-hourglass',
                      view_name='catalog_history'),
            ]
        )
        ret.update({
            'sidebar_items': sidebar_items,
            'sidebar_selected': '%s-%d' % (kind,
                    model_type_id) if model_type_id else '',
            'kind': kind,
            'component_model_types': ComponentType(item=lambda a: a),
            'device_model_types': DeviceType(item=lambda a: a),
            'model_type_id': model_type_id,
            'subsection': model_type_id,
            'details': self.kwargs.get('details', 'info'),
            'editable': True,
        })
        return ret


class CatalogDevice(Catalog):
    template_name = 'ui/catalog-device.html'

    def __init__(self, *args, **kwargs):
        super(CatalogDevice, self).__init__(*args, **kwargs)
        self.form = None

    def update_cached(self, group):
        for device in Device.objects.filter(model__group=group):
            pricing.device_update_cached(device)

    def post(self, *args, **kwargs):
        if not self.request.user.get_profile().has_perm(
                Perm.edit_device_info_financial):
            raise HttpResponseForbidden(
                    "You have no permission to edit catalog")
        if 'move' in self.request.POST:
            items = self.request.POST.getlist('items')
            if not items:
                messages.error(self.request, "Nothing to move.")
                return HttpResponseRedirect(self.request.path)
            target_id = self.request.POST.get('target', '')
            if target_id == 'none':
                target = None
            elif target_id == 'new':
                item = get_object_or_404(DeviceModel, id=items[0])
                target = DeviceModelGroup(name=item.name, type=item.type)
                target.save(user=self.request.user)
            else:
                target = get_object_or_404(DeviceModelGroup, id=target_id)
            for item in items:
                model = get_object_or_404(DeviceModel, id=item)
                model.group = target
                model.save(user=self.request.user)
            self.update_cached(target)
            messages.success(self.request, "Items moved.")
            return HttpResponseRedirect(self.request.path)
        elif 'delete' in self.request.POST:
            try:
                self.group_id = int(self.kwargs.get('group', ''))
            except ValueError:
                messages.error(self.request, "No such group.")
            else:
                self.group = get_object_or_404(DeviceModelGroup,
                                               id=self.group_id)
                self.group.price = 0
                self.group.save(user=self.request.user)
                self.update_cached(self.group)
                self.group.delete()
                messages.warning(self.request,
                                 "Group '%s' deleted." % self.group.name)
            return HttpResponseRedirect(self.request.path+'..')
        else:
            try:
                self.group_id = int(self.kwargs.get('group', ''))
            except ValueError:
                self.group_id = None
                self.group = None
            else:
                self.group = get_object_or_404(DeviceModelGroup,
                                               id=self.group_id)
            self.form = DeviceModelGroupForm(self.request.POST,
                                             instance=self.group)
            if self.form.is_valid():
                self.form.save(commit=False)
                self.form.instance.save(user=self.request.user)
                self.update_cached(self.group)
                messages.success(self.request, "Changes saved.")
                return HttpResponseRedirect(self.request.path)
            else:
                messages.error(self.request, "Correct the errors.")
        return self.get(*args, **kwargs)

    def get(self, *args, **kwargs):
        try:
            self.model_type_id = int(self.kwargs.get('type', ''))
        except ValueError:
            self.model_type_id = None
        try:
            self.group_id = int(self.kwargs.get('group', ''))
        except ValueError:
            self.group_id = None
            self.group = None
        else:
            self.group = get_object_or_404(DeviceModelGroup, id=self.group_id)
        if self.group:
            self.query = self.group.devicemodel_set.all()
        else:
            self.query = DeviceModel.objects.filter(
                    type=self.model_type_id).filter(group=None)
        self.unassigned_count = DeviceModel.objects.filter(
                type=self.model_type_id
            ).filter(
                group=None
            ).count()
        self.groups = list(DeviceModelGroup.objects.filter(
            type=self.model_type_id))
        for g in self.groups:
            g.count = g.get_count()
        if not self.form:
            self.form = DeviceModelGroupForm(instance=self.group)
        return super(CatalogDevice, self).get(*args, **kwargs)

    def get_context_data(self, **kwargs):
        ret = super(CatalogDevice, self).get_context_data(**kwargs)
        ret.update({
            'columns': ['count', 'size'],
            'groups': self.groups,
            'group': self.group,
            'unassigned_count': self.unassigned_count,
            'form': self.form,
        })
        ret.update(_prepare_model_groups(self.request, self.query))
        return ret

class CatalogComponent(Catalog):
    template_name = 'ui/catalog-component.html'

    def __init__(self, *args, **kwargs):
        super(CatalogComponent, self).__init__(*args, **kwargs)
        self.form = None

    def update_cached(self, group):
        devices = set()
        for _class in (Storage, Memory, Processor, DiskShare, FibreChannel,
                       GenericComponent, OperatingSystem, Software):
            for component in _class.objects.filter(model__group=group):
                devices.add(component.device)
        for device in devices:
            pricing.device_update_cached(device)

    def post(self, *args, **kwargs):
        if not self.request.user.get_profile().has_perm(
                Perm.edit_device_info_financial):
            raise HttpResponseForbidden(
                    "You have no permission to edit catalog")
        if 'move' in self.request.POST:
            items = self.request.POST.getlist('items')
            if not items:
                messages.error(self.request, "Nothing to move.")
                return HttpResponseRedirect(self.request.path)
            target_id = self.request.POST.get('target', '')
            if target_id == 'none':
                target = None
            elif target_id == 'new':
                item = get_object_or_404(ComponentModel, id=items[0])
                target = ComponentModelGroup(name=item.name, type=item.type)
                target.save(user=self.request.user)
            else:
                target = get_object_or_404(ComponentModelGroup, id=target_id)
            for item in items:
                model = get_object_or_404(ComponentModel, id=item)
                model.group = target
                model.save(user=self.request.user)
            self.update_cached(target)
            messages.success(self.request, "Items moved.")
            return HttpResponseRedirect(self.request.path)
        elif 'delete' in self.request.POST:
            try:
                self.group_id = int(self.kwargs.get('group', ''))
            except ValueError:
                messages.error(self.request, "No such group.")
            else:
                self.group = get_object_or_404(ComponentModelGroup,
                                               id=self.group_id)
                self.group.price = 0
                self.group.save(user=self.request.user)
                self.update_cached(self.group)
                self.group.delete()
                messages.warning(self.request,
                                 "Group '%s' deleted." % self.group.name)
            return HttpResponseRedirect(self.request.path+'..')
        else:
            try:
                self.group_id = int(self.kwargs.get('group', ''))
            except ValueError:
                self.group_id = None
                self.group = None
            else:
                self.group = get_object_or_404(ComponentModelGroup,
                                               id=self.group_id)
            self.form = ComponentModelGroupForm(self.request.POST,
                                                instance=self.group)
            if self.form.is_valid():
                self.form.save(commit=False)
                self.form.instance.save(user=self.request.user)
                self.update_cached(self.group)
                messages.success(self.request, "Changes saved.")
                return HttpResponseRedirect(self.request.path)
            else:
                messages.error(self.request, "Correct the errors.")
        return self.get(*args, **kwargs)


    def get(self, *args, **kwargs):
        try:
            self.model_type_id = int(self.kwargs.get('type', ''))
        except ValueError:
            self.model_type_id = None
        try:
            self.group_id = int(self.kwargs.get('group', ''))
        except ValueError:
            self.group_id = None
            self.group = None
        else:
            self.group = get_object_or_404(ComponentModelGroup,
                                           id=self.group_id)
        if self.group:
            self.query = self.group.componentmodel_set.all()
        else:
            self.query = ComponentModel.objects.filter(
                    type=self.model_type_id).filter(group=None)
        self.unassigned_count = ComponentModel.objects.filter(
                type=self.model_type_id
            ).filter(
                group=None
            ).count()
        groups = list(ComponentModelGroup.objects.filter(
                type=self.model_type_id))
        for g in groups:
            g.count = g.get_count()
            g.modified_price = decimal.Decimal(
                    g.price or 0) / (g.size_modifier or 1)
        self.groups = groups
        if not self.form:
            self.form = ComponentModelGroupForm(instance=self.group)
        return super(CatalogComponent, self).get(*args, **kwargs)

    def get_context_data(self, **kwargs):
        ret = super(CatalogComponent, self).get_context_data(**kwargs)
        ret.update({
            'columns': ['count'],
            'groups': self.groups,
            'group': self.group,
            'unassigned_count': self.unassigned_count,
            'form': self.form,
            'CURRENCY': settings.CURRENCY,
        })
        ret.update(_prepare_model_groups(self.request, self.query))
        return ret


class CatalogHistory(Catalog):
    template_name = 'ui/catalog-history.html'

    def get_context_data(self, **kwargs):
        ret = super(CatalogHistory, self).get_context_data(**kwargs)
        query = HistoryModelChange.objects.all()
        query, sort, page = _prepare_query(self.request, query, False,
                                           HISTORY_SORT_COLUMNS, '-date')
        if page == 0:
            pages = Paginator(query, MAX_PAGE_SIZE)
            items = pages.page(1)
        else:
            pages = Paginator(query, PAGE_SIZE)
            items = pages.page(page)
        ret.update({
            'sidebar_selected': 'history',
            'subsection': 'history',
            'sort': sort,
            'items': items,
        })
        return ret
