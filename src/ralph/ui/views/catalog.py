# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import decimal
import calendar
import cStringIO
import datetime

from bob.csvutil import UnicodeReader
from bob.menu import MenuItem, MenuHeader
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import models as db
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.conf import settings
from lck.django.common import nested_commit_on_success

from ralph.account.models import Perm
from ralph.discovery.models import (
    ComponentModel,
    ComponentModelGroup,
    ComponentType,
    Device,
    DeviceModel,
    DeviceModelGroup,
    DeviceType,
    DiskShare,
    FibreChannel,
    GenericComponent,
    Memory,
    OperatingSystem,
    Processor,
    Software,
    Storage,
    PricingGroup,
    PricingValue,
    PricingVariable,
)
from ralph.discovery.models_history import HistoryModelChange
from ralph.ui.forms.catalog import (
    ComponentModelGroupForm,
    DeviceModelGroupForm,
    PricingGroupForm,
    PricingVariableFormSet,
    PricingDeviceForm,
    PricingValueFormSet,
    PricingFormulaFormSet,
)
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
    template_name = 'ui/catalog/base.html'

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
            [
                MenuHeader('Component groups'),
            ] + [
                MenuItem(
                    label=t.raw.title(),
                    name='component-%d' % t.id,
                    fugue_icon=COMPONENT_ICONS.get(t.id),
                    view_name='catalog',
                    view_args=('component', t.id),
                ) for t in ComponentType(item=lambda t: t)
            ] + [
                MenuHeader('Device groups'),
            ] + [
                MenuItem(
                    label=t.raw.title(),
                    name='device-%d' % t.id,
                    fugue_icon=DEVICE_ICONS.get(t.id),
                    view_name='catalog',
                    view_args=('device', t.id),
                ) for t in DeviceType(item=lambda t: t)
            ] + [
                MenuHeader('Tools'),
                MenuItem(
                    'History',
                    name='history',
                    fugue_icon='fugue-hourglass',
                    view_name='catalog_history',
                ),
                MenuItem(
                    'Pricing groups',
                    name='pricing',
                    fugue_icon='fugue-shopping-basket',
                    view_name='catalog_pricing',
                    view_args=('pricing',),
                ),
            ]
        )
        selected = '%s-%d' % (kind, model_type_id) if model_type_id else ''
        ret.update({
            'component_model_types': ComponentType(item=lambda a: a),
            'details': self.kwargs.get('details', 'info'),
            'device_model_types': DeviceType(item=lambda a: a),
            'editable': True,
            'kind': kind,
            'model_type_id': model_type_id,
            'sidebar_items': sidebar_items,
            'sidebar_selected': selected,
            'subsection': model_type_id,
        })
        return ret


class CatalogDevice(Catalog):
    template_name = 'ui/catalog/device.html'

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
        elif 'clear' in self.request.POST:
            items = self.request.POST.getlist('items')
            if not items:
                messages.error(self.request, "Nothing to clear.")
                return HttpResponseRedirect(self.request.path)
            for item in items:
                model = get_object_or_404(DeviceModel, id=item)
                priorities = model.get_save_priorities()
                priorities = dict((key, 0) for key in priorities)
                model.update_save_priorities(priorities)
                model.save(user=self.request.user)
            messages.success(self.request, "Items cleaned.")
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
            return HttpResponseRedirect(self.request.path + '..')
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
        unassigned_devices = DeviceModel.objects.filter(
            type=self.model_type_id
        ).filter(
            group=None
        )
        unassigned_count = 0
        for u in unassigned_devices:
            unassigned_count = unassigned_count + u.get_count()
        self.unassigned_count = unassigned_count
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
    template_name = 'ui/catalog/component.html'

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
        elif 'clear' in self.request.POST:
            items = self.request.POST.getlist('items')
            if not items:
                messages.error(self.request, "Nothing to clear.")
                return HttpResponseRedirect(self.request.path)
            for item in items:
                model = get_object_or_404(ComponentModel, id=item)
                priorities = model.get_save_priorities()
                priorities = dict((key, 0) for key in priorities)
                model.update_save_priorities(priorities)
                model.save(user=self.request.user)
            messages.success(self.request, "Items cleaned.")
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
            return HttpResponseRedirect(self.request.path + '..')
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
        unassigned_components = ComponentModel.objects.filter(
            type=self.model_type_id
        ).filter(
            group=None
        )
        unassigned_count = 0
        for u in unassigned_components:
            unassigned_count = unassigned_count + u.get_count()
        self.unassigned_count = unassigned_count
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
    template_name = 'ui/catalog/history.html'

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


class CatalogPricing(Catalog):
    template_name = 'ui/catalog/pricing.html'

    def parse_args(self):
        self.today = datetime.date.today()
        self.year = int(self.kwargs.get('year', self.today.year))
        self.month = int(self.kwargs.get('month', self.today.month))
        self.group_name = self.kwargs.get('group', '')
        self.date = datetime.date(self.year, self.month, 1)

    def get_context_data(self, **kwargs):
        ret = super(CatalogPricing, self).get_context_data(**kwargs)
        self.parse_args()
        date = datetime.date(self.year, self.month, 1)
        group_items = [
            MenuItem(
                'Add a new group',
                name='',
                fugue_icon='fugue-shopping-basket--plus',
                view_name='catalog_pricing',
                view_args=(
                    'pricing',
                    '%04d' % self.year,
                    '%02d' % self.month
                ),
            ),
        ] + [
            MenuItem(
                g.name,
                name=g.name,
                fugue_icon = 'fugue-shopping-basket',
                view_name='catalog_pricing',
                view_args=(
                    'pricing',
                    '%04d' % self.year,
                    '%02d' % self.month,
                    g.name,
                ),
            ) for g in PricingGroup.objects.filter(date=date)
        ]
        aggr = PricingGroup.objects.aggregate(db.Min('date'))
        min_year = aggr['date__min'].year if aggr['date__min'] else self.year
        aggr = PricingGroup.objects.aggregate(db.Max('date'))
        max_year = aggr['date__max'].year if aggr['date__max'] else self.year
        min_year = min(self.year, self.today.year, min_year)
        max_year = max(self.year, self.today.year, max_year)
        ret.update({
            'sidebar_selected': 'pricing',
            'subsection': 'pricing',
            'group_items': group_items,
            'year': self.year,
            'month': self.month,
            'months': list(enumerate(calendar.month_abbr))[1:],
            'years': range(min_year - 1, max_year + 2),
            'today': self.today,
            'group_name': self.group_name,
        })
        return ret


class CatalogPricingNew(CatalogPricing):

    def __init__(self, *args, **kwargs):
        super(CatalogPricingNew, self).__init__(*args, **kwargs)
        self.form = None

    def post(self, *args, **kwargs):
        self.parse_args()
        self.form = PricingGroupForm(
            self.date,
            self.request.POST,
            self.request.FILES,
        )
        if self.form.is_valid():
            self.form.save(commit=False)
            self.form.instance.date = datetime.date(self.year, self.month, 1)
            self.form.instance.save()
            if self.form.cleaned_data['clone']:
                sources = PricingGroup.objects.filter(
                    name=self.form.instance.name,
                    date__lt=self.form.instance.date,
                ).order_by('-date')[:1]
                if sources.exists():
                    self.form.instance.clone_contents(sources[0])
            elif self.form.cleaned_data['upload']:
                self.import_csv(
                    self.form.instance,
                    self.request.FILES['upload']
                )
            messages.success(
                self.request,
                "Group %s saved." % self.form.instance.name
            )
            return HttpResponseRedirect(self.request.path)
        messages.error(self.request, "Errors in the form.")
        return self.get(*args, **kwargs)

    @nested_commit_on_success
    def import_csv(self, group, uploaded_file):
        if uploaded_file.size > 4 * 1024 * 1024:
            messages.error(self.request, "File too big to import.")
            return
        f = cStringIO.StringIO(uploaded_file.read())
        rows = iter(UnicodeReader(f))
        header = list(rows.next())
        if header[0].strip() != 'sn':
            messages.error(
                self.request,
                "The first row should have 'sn' followed by variable names."
            )
            return
        variables = [name.strip() for name in header[1:]]
        devices = {}
        try:
            for row in rows:
                if not row:
                    continue
                devices[row[0]] = dict(zip(
                    variables,
                    (decimal.Decimal(v) for v in row[1:]),
                ))
        except ValueError as e:
            messages.error(self.request, "Invalid value: %s." % e)
            return
        variable_dict = {}
        for name in variables:
            v = PricingVariable(name=name, group=group)
            v.save()
            variable_dict[name] = v
        for sn, values in devices.iteritems():
            try:
                device = Device.objects.get(sn=sn)
            except Device.DoesNotExist:
                messages.warning(
                    self.request,
                    "Serial number %s not found, skipping." % sn
                )
                continue
            group.devices.add(device)
            for name, value in values.iteritems():
                PricingValue(
                    variable=variable_dict[name],
                    device=device,
                    value=value,
                ).save()
        group.save()

    def get_context_data(self, **kwargs):
        ret = super(CatalogPricingNew, self).get_context_data(**kwargs)
        self.parse_args()
        if self.form is None:
            self.form = PricingGroupForm(self.date)
        ret.update({
            'form': self.form,
            'group_name': '',
        })
        return ret


class CatalogPricingGroup(CatalogPricing):

    def __init__(self, *args, **kwargs):
        super(CatalogPricingGroup, self).__init__(*args, **kwargs)
        self.variables_formset = None
        self.device_form = None
        self.devices = None
        self.formulas_formset = None

    def get_devices(self, group, variables, post=None):
        devices = list(group.devices.all())
        for device in devices:
            values = device.pricingvalue_set.filter(
                variable__group=group,
            ).order_by(
                'variable__name',
            )
            device.formset = PricingValueFormSet(
                post,
                queryset=values,
                prefix='values-%d' % device.id,
            )
        return devices

    def post(self, *args, **kwargs):
        if 'values-save' in self.request.POST:
            return self.handle_values_form(*args, **kwargs)
        elif 'formulas-save' in self.request.POST:
            return self.handle_formulas_form(*args, **kwargs)
        elif 'group-delete' in self.request.POST:
            self.parse_args()
            get_object_or_404(
                PricingGroup,
                name=self.group_name,
                date=self.date,
            ).delete()
        return self.get(*args, **kwargs)

    def handle_formulas_form(self, *args, **kwargs):
        self.parse_args()
        group = get_object_or_404(
            PricingGroup,
            name=self.group_name,
            date=self.date,
        )
        self.formulas_formset = PricingFormulaFormSet(
            group,
            self.request.POST,
            queryset=group.pricingformula_set.all(),
            prefix='formulas',
        )
        if not self.formulas_formset.is_valid():
            messages.error(self.request, "Errors in the formulas form.")
            return self.get(*args, **kwargs)
        for form in self.formulas_formset.extra_forms:
            if form.has_changed():
                form.instance.group = group
        self.formulas_formset.save()
        messages.success(self.request, "Group %s saved." % group.name)
        return HttpResponseRedirect(self.request.path)

    def handle_values_form(self, *args, **kwargs):
        self.parse_args()
        group = get_object_or_404(
            PricingGroup,
            name=self.group_name,
            date=self.date,
        )
        self.variables_formset = PricingVariableFormSet(
            self.request.POST,
            queryset=group.pricingvariable_set.all(),
            prefix='variables',
        )
        self.device_form = PricingDeviceForm(self.request.POST)
        variables = group.pricingvariable_set.order_by('name')
        self.devices = self.get_devices(group, variables, self.request.POST)
        values_formsets = [d.formset for d in self.devices]
        if not all([
            self.variables_formset.is_valid(),
            self.device_form.is_valid(),
            all(fs.is_valid() for fs in values_formsets),
        ]):
            messages.error(self.request, "Errors in the variables form.")
            return self.get(*args, **kwargs)
        for device in self.devices:
            device.formset.save()
        for name in self.request.POST:
            if name.startswith('device-delete-'):
                device_id = int(name[len('device-delete-'):])
                device = get_object_or_404(Device, id=device_id)
                group.devices.remove(device)
                device.pricingvalue_set.filter(variable__group=group).delete()
                group.save()
        for form in self.variables_formset.extra_forms:
            if form.has_changed():
                form.instance.group = group
        self.variables_formset.save()
        for form in self.variables_formset.extra_forms:
            if form.has_changed():
                for device in self.devices:
                    value = PricingValue(
                        device=device,
                        variable=form.instance,
                        value=0,
                    )
                    value.save()
        device = self.device_form.cleaned_data['device']
        if device:
            if group.devices.filter(id=device.id).exists():
                messages.warning(
                    self.request,
                    "Device %s is already in group %s." % (
                        device.name,
                        group.name,
                    ),
                )
            else:
                group.devices.add(device)
                group.save()
                for variable in variables.all():
                    value = PricingValue(
                        device=device,
                        variable=variable,
                        value=0,
                    )
                    value.save()
                messages.success(
                    self.request,
                    "Device %s added to group %s." % (device.name, group.name),
                )
        messages.success(self.request, "Group %s saved." % group.name)
        return HttpResponseRedirect(self.request.path)

    def get_context_data(self, **kwargs):
        ret = super(CatalogPricingGroup, self).get_context_data(**kwargs)
        try:
            group = PricingGroup.objects.get(
                name=self.group_name,
                date=self.date,
            )
        except PricingGroup.DoesNotExist:
            group = None
        else:
            variables = group.pricingvariable_set.order_by('name')
            if self.variables_formset is None:
                self.variables_formset = PricingVariableFormSet(
                    queryset=variables,
                    prefix='variables',
                )
            if self.device_form is None:
                self.device_form = PricingDeviceForm()
            if self.devices is None:
                self.devices = self.get_devices(group, variables)
            if self.formulas_formset is None:
                self.formulas_formset = PricingFormulaFormSet(
                    group,
                    queryset=group.pricingformula_set.all(),
                    prefix='formulas',
                )
        ret.update({
            'devices': self.devices,
            'variablesformset': self.variables_formset,
            'deviceform': self.device_form,
            'formulasformset': self.formulas_formset,
            'group': group,
        })
        return ret
