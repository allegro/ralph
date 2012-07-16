# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect
from django.http import HttpResponseForbidden
from django.contrib import messages

from ralph.ui.views.common import Base
from ralph.discovery.models import (DeviceType, ComponentType, DeviceModel,
        DeviceModelGroup, ComponentModelGroup, ComponentModel)
from ralph.ui.forms import ComponentModelGroupForm, DeviceModelGroupForm
from ralph.account.models import Perm

MODEL_GROUP_SORT_COLUMNS = {
    'name': ('name',),
    'size': ('chassis_size',),
}
PAGE_SIZE = 25
MAX_PAGE_SIZE = 65535


def _get_pages(paginator, page):
    pages = paginator.page_range[max(0, page - 2):min(paginator.num_pages, page + 1)]
    if 1 not in pages:
        pages.insert(0, 1)
        pages.insert(1, '...')
    if paginator.num_pages not in pages:
        pages.append('...')
        pages.append(paginator.num_pages)
    return pages

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
    if sort in ('count', '-count'):
        query = list(query)
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
        'pages': _get_pages(pages, page),
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
        ret.update({
            'kind': self.kwargs.get('kind'),
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

    def post(self, *args, **kwargs):
        if not self.request.user.get_profile().has_perm(
                Perm.edit_device_info_financial):
            raise HttpResponseForbidden('You have no permission to edit catalog')
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
                target.save()
            else:
                target = get_object_or_404(DeviceModelGroup, id=target_id)
            for item in items:
                model = get_object_or_404(DeviceModel, id=item)
                model.group = target
                model.save()
            messages.success(self.request, "Items moved.")
            return HttpResponseRedirect(self.request.path)
        elif 'delete' in self.request.POST:
            try:
                self.group_id = int(self.kwargs.get('group', ''))
            except ValueError:
                messages.error(self.request, "No such group.")
            else:
                self.group = get_object_or_404(DeviceModelGroup, id=self.group_id)
                messages.warning(self.request, "Group '%s' deleted." % self.group.name)
                self.group.delete()
            return HttpResponseRedirect(self.request.path+'..')
        else:
            try:
                self.group_id = int(self.kwargs.get('group', ''))
            except ValueError:
                self.group_id = None
                self.group = None
            else:
                self.group = get_object_or_404(DeviceModelGroup, id=self.group_id)
            self.form = DeviceModelGroupForm(self.request.POST, instance=self.group)
            if self.form.is_valid():
                self.form.save()
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
        self.groups = DeviceModelGroup.objects.filter(type=self.model_type_id)
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

    def post(self, *args, **kwargs):
        if not self.request.user.get_profile().has_perm(
                Perm.edit_device_info_financial):
            raise HttpResponseForbidden('You have no permission to edit catalog')
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
                target.save()
            else:
                target = get_object_or_404(ComponentModelGroup, id=target_id)
            for item in items:
                model = get_object_or_404(ComponentModel, id=item)
                model.group = target
                model.save()
            messages.success(self.request, "Items moved.")
            return HttpResponseRedirect(self.request.path)
        elif 'delete' in self.request.POST:
            try:
                self.group_id = int(self.kwargs.get('group', ''))
            except ValueError:
                messages.error(self.request, "No such group.")
            else:
                self.group = get_object_or_404(ComponentModelGroup, id=self.group_id)
                messages.warning(self.request, "Group '%s' deleted." % self.group.name)
                self.group.delete()
            return HttpResponseRedirect(self.request.path+'..')
        else:
            try:
                self.group_id = int(self.kwargs.get('group', ''))
            except ValueError:
                self.group_id = None
                self.group = None
            else:
                self.group = get_object_or_404(ComponentModelGroup, id=self.group_id)
            self.form = ComponentModelGroupForm(self.request.POST, instance=self.group)
            if self.form.is_valid():
                self.form.save()
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
            self.group = get_object_or_404(ComponentModelGroup, id=self.group_id)
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
        self.groups = ComponentModelGroup.objects.filter(type=self.model_type_id)
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
        })
        ret.update(_prepare_model_groups(self.request, self.query))
        return ret
