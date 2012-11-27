# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import re

from bob.menu import MenuItem, MenuHeader
from django.contrib import messages
from django.db import IntegrityError, transaction
from django.http import HttpResponseRedirect, Http404
from django.forms.models import modelformset_factory
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _
from lck.django.common import nested_commit_on_success

from ralph.assets.forms import (
    AddDeviceForm, AddPartForm, EditDeviceForm,
    EditPartForm, BaseDeviceForm, OfficeForm,
    BasePartForm, BaseAssetForm
)
from ralph.assets.models import (
    DeviceInfo, AssetSource, Asset, OfficeInfo, PartInfo,
)
from ralph.ui.views.common import Base
from ralph.assets.forms import SearchAssetForm
from django.db.models import Q


class AssetsMixin(Base):
    template_name = "assets/base.html"

    def get(self, *args, **kwargs):
        # TODO
        return super(AssetsMixin, self).get(*args, **kwargs)

    def post(self, *args, **kwargs):
        # TODO
        return super(AssetsMixin, self).post(*args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        ret = super(AssetsMixin, self).get_context_data(**kwargs)
        ret.update({
            'sidebar_items': self.get_sidebar_items(),
            'mainmenu_items': self.get_mainmenu_items(),
            'section': 'assets',
            'sidebar_selected': self.sidebar_selected,
            'section': self.mainmenu_selected,
        })

        return ret

    def get_mainmenu_items(self):
        return [
            MenuItem(
                label='Data center',
                name='dc',
                fugue_icon='fugue-building',
                href='/assets/dc',
            ),
            MenuItem(
                label='BackOffice',
                fugue_icon='fugue-printer',
                name='back_office',
                href='/assets/back_office',
            ),
        ]


class DataCenterMixin(AssetsMixin):
    mainmenu_selected = 'dc'

    def get_sidebar_items(self):
        items = (
            ('/assets/dc/add/device/', 'Add device', 'fugue-block--plus'),
            ('/assets/dc/add/part/', 'Add part', 'fugue-block--plus'),
            ('/assets/dc/search', 'Search', 'fugue-magnifier'),
        )
        sidebar_menu = (
            [MenuHeader('Data center actions')] +
            [MenuItem(
             label=t[1],
             fugue_icon=t[2],
             href=t[0]
             ) for t in items]
        )
        return sidebar_menu


class BackOfficeMixin(AssetsMixin):
    mainmenu_selected = 'back_office'

    def get_sidebar_items(self):
        items = (
                ('/assets/back_office/add/device/', 'Add device',
                 'fugue-block--plus'),
                ('/assets/back_office/add/part/', 'Add part',
                 'fugue-block--plus'),
                ('/assets/back_office/search', 'Search', 'fugue-magnifier'),
        )
        sidebar_menu = (
            [MenuHeader('Back office actions')] +
            [MenuItem(
                label=t[1],
                fugue_icon=t[2],
                href=t[0]
            ) for t in items]
        )
        return sidebar_menu


class AssetSearch(AssetsMixin):
    def handle_search_data(self):
        search_fields = [
            'model', 'invoice_no', 'order_no', 'buy_date',
            'provider', 'status', 'sn'
        ]
        all_q = Q()
        for field in search_fields:
            field_value = self.request.GET.get(field)
            if field_value:
                q = Q(**{'%s' % field: field_value})
                all_q = all_q & q
        return self.get_all_items(all_q)

    def get_all_items(self, query):
        return Asset.objects().filter(query)

    def get_context_data(self, *args, **kwargs):
        ret = super(AssetSearch, self).get_context_data(*args, **kwargs)
        ret.update({
            'form': self.form,
            'data': self.data,
            'header': self.header,
        })
        return ret

    def get(self, *args, **kwargs):
        self.form = SearchAssetForm(self.request.GET)
        self.data = self.handle_search_data()
        return super(AssetSearch, self).get(*args, **kwargs)


class BackOfficeSearch(BackOfficeMixin, AssetSearch):
    header = 'Search BO Assets'
    sidebar_selected = 'search'
    template_name = 'assets/search_asset.html'

    def get_all_items(self, query):
        return Asset.objects_bo().filter(query)


class DataCenterSearch(DataCenterMixin, AssetSearch):
    header = 'Search DC Assets'
    sidebar_selected = 'search'
    template_name = 'assets/search_asset.html'

    def get_all_items(self, query):
        return Asset.objects_dc().filter(query)


def _get_mode(request):
    current_url = request.get_full_path()
    return 'back_office' if 'back_office' in current_url else 'dc'


def _get_return_link(request):
    return "/assets/%s/" % _get_mode(request)


class AddDevice(Base):
    template_name = 'assets/add_device.html'

    def get_context_data(self, **kwargs):
        ret = super(AddDevice, self).get_context_data(**kwargs)
        ret.update({
            'asset_form': self.asset_form,
            'device_info_form': self.device_info_form,
            'form_id': 'add_device_asset_form',
            'edit_mode': False,
        })
        return ret

    def get(self, *args, **kwargs):
        self.asset_form = AddDeviceForm(mode=_get_mode(self.request))
        self.device_info_form = BaseDeviceForm()
        return super(AddDevice, self).get(*args, **kwargs)

    def post(self, *args, **kwargs):
        self.asset_form = AddDeviceForm(
            self.request.POST, mode=_get_mode(self.request))
        self.device_info_form = BaseDeviceForm(self.request.POST)
        if self.asset_form.is_valid() and self.device_info_form.is_valid():
            transaction.enter_transaction_management()
            transaction.managed()
            transaction.commit()
            asset_data = {}
            for f_name, f_value in self.asset_form.cleaned_data.items():
                if f_name in ["barcode", "sn"]:
                    continue
                asset_data[f_name] = f_value
            asset_data['source'] = AssetSource.shipment
            serial_numbers = self.asset_form.cleaned_data['sn']
            serial_numbers = filter(
                len, re.split(",|\n", serial_numbers))
            barcodes = self.asset_form.cleaned_data['barcode']
            if barcodes:
                barcodes = filter(
                    len, re.split(",|\n", barcodes))
            i = 0
            duplicated_sn = []
            duplicated_barcodes = []
            for sn in serial_numbers:
                device_info = DeviceInfo(
                    warehouse=self.device_info_form.cleaned_data['warehouse'],
                    size=self.device_info_form.cleaned_data['size']
                )
                device_info.save()
                asset = Asset(
                    device_info=device_info,
                    sn=sn.strip(),
                    **asset_data
                )
                if barcodes:
                    asset.barcode = barcodes[i].strip()
                try:
                    asset.save()
                except IntegrityError as e:
                    if "'sn'" in e[1]:
                        duplicated_sn.append(asset.sn)
                    if barcodes and "'barcode'" in e[1]:
                        duplicated_barcodes.append(asset.barcode)
                i += 1
            if duplicated_sn or duplicated_barcodes:
                transaction.rollback()
                msg = ""
                if duplicated_sn:
                    msg = "Serial numbers with duplicates: %s. " % (
                        ", ".join(duplicated_sn))
                if duplicated_barcodes:
                    msg += "Barcodes with duplicates: %s. " % (
                        ", ".join(duplicated_barcodes))
                messages.warning(self.request, msg)
            else:
                transaction.commit()
                transaction.managed(False)
                messages.success(self.request, _("Assets saved."))
                return HttpResponseRedirect(_get_return_link(self.request))
        else:
            messages.error(self.request, _("Please correct the errors."))
        return super(AddDevice, self).get(*args, **kwargs)


class BackOfficeAddDevice(AddDevice, BackOfficeMixin):
    sidebar_selected = 'add device'


class DataCenterAddDevice(AddDevice, DataCenterMixin):
    sidebar_selected = 'add device'


class AddPart(Base):
    template_name = 'assets/add_part.html'

    def get_context_data(self, **kwargs):
        ret = super(AddPart, self).get_context_data(**kwargs)
        ret.update({
            'asset_form': self.asset_form,
            'part_info_form': self.part_info_form,
            'form_id': 'add_part_form',
            'edit_mode': False,
        })
        return ret

    def get(self, *args, **kwargs):
        self.asset_form = AddPartForm(mode=_get_mode(self.request))
        self.part_info_form = BasePartForm()
        return super(AddPart, self).get(*args, **kwargs)

    def post(self, *args, **kwargs):
        self.asset_form = AddPartForm(
            self.request.POST, mode=_get_mode(self.request))
        self.part_info_form = BasePartForm(self.request.POST)
        if self.asset_form.is_valid() and self.part_info_form.is_valid():
            transaction.enter_transaction_management()
            transaction.managed()
            transaction.commit()
            asset_data = {}
            for f_name, f_value in self.asset_form.cleaned_data.items():
                if f_name in ["sn"]:
                    continue
                asset_data[f_name] = f_value
            asset_data['source'] = AssetSource.shipment
            asset_data['barcode'] = None
            serial_numbers = self.asset_form.cleaned_data['sn']
            serial_numbers = filter(len, re.split(",|\n", serial_numbers))
            duplicated_sn = []
            for sn in serial_numbers:
                part_info = PartInfo(**self.part_info_form.cleaned_data)
                part_info.save()
                asset = Asset(
                    part_info=part_info,
                    sn=sn.strip(),
                    **asset_data
                )
                try:
                    asset.save()
                except IntegrityError as e:
                    if "'sn'" in e[1]:
                        duplicated_sn.append(asset.sn)
            if duplicated_sn:
                transaction.rollback()
                msg = "Serial numbers with duplicates: %s." % (
                    ", ".join(duplicated_sn))
                messages.warning(self.request, msg)
            else:
                transaction.commit()
                transaction.managed(False)
                messages.success(self.request, _("Assets saved."))
                return HttpResponseRedirect(_get_return_link(self.request))
        else:
            messages.error(self.request, _("Please correct the errors."))
        return super(AddPart, self).get(*args, **kwargs)


class BackOfficeAddPart(AddPart, BackOfficeMixin):
    sidebar_selected = 'add part'


class DataCenterAddPart(AddPart, DataCenterMixin):
    sidebar_selected = 'add part'


class EditDevice(Base):
    template_name = 'assets/edit_device.html'

    def get_context_data(self, **kwargs):
        ret = super(EditDevice, self).get_context_data(**kwargs)
        ret.update({
            'asset_form': self.asset_form,
            'device_info_form': self.device_info_form,
            'office_info_form': self.office_info_form,
            'form_id': 'edit_device_asset_form',
            'edit_mode': True,
        })
        return ret

    def get(self, *args, **kwargs):
        asset = get_object_or_404(Asset, id=kwargs.get('asset_id'))
        if not asset.device_info:  # it isn't device asset
            raise Http404()
        self.asset_form = EditDeviceForm(
            instance=asset, mode=_get_mode(self.request))
        self.device_info_form = BaseDeviceForm(instance=asset.device_info)
        self.office_info_form = OfficeForm(instance=asset.office_info)
        return super(EditDevice, self).get(*args, **kwargs)

    @nested_commit_on_success
    def post(self, *args, **kwargs):
        asset = get_object_or_404(Asset, id=kwargs.get('asset_id'))
        self.asset_form = EditDeviceForm(
            self.request.POST, instance=asset, mode=_get_mode(self.request))
        self.device_info_form = BaseDeviceForm(self.request.POST)
        self.office_info_form = OfficeForm(
            self.request.POST, self.request.FILES)
        if all((
            self.asset_form.is_valid(),
            self.device_info_form.is_valid(),
            self.office_info_form.is_valid()
        )):
            asset_data = self.asset_form.cleaned_data
            if not asset_data['barcode']:
                asset_data['barcode'] = None
            asset.__dict__.update(**asset_data)
            if not asset.office_info:
                office_info = OfficeInfo()
            else:
                office_info = asset.office_info
            office_info.__dict__.update(**self.office_info_form.cleaned_data)
            office_info.save()
            asset.office_info = office_info
            asset.device_info.__dict__.update(
                **self.device_info_form.cleaned_data)
            asset.device_info.save()
            asset.save()
            return HttpResponseRedirect(_get_return_link(self.request))
        else:
            messages.error(self.request, _("Please correct the errors."))
        return super(EditDevice, self).get(*args, **kwargs)


class BackOfficeEditDevice(EditDevice, BackOfficeMixin):
    sidebar_selected = None


class DataCenterEditDevice(EditDevice, DataCenterMixin):
    sidebar_selected = None


class EditPart(Base):
    template_name = 'assets/edit_part.html'

    def get_context_data(self, **kwargs):
        ret = super(EditPart, self).get_context_data(**kwargs)
        ret.update({
            'asset_form': self.asset_form,
            'office_info_form': self.office_info_form,
            'form_id': 'edit_part_form',
            'edit_mode': True,
        })
        return ret

    def get(self, *args, **kwargs):
        asset = get_object_or_404(Asset, id=kwargs.get('asset_id'))
        if asset.device_info:  # it isn't part asset
            raise Http404()
        self.asset_form = EditPartForm(
            instance=asset, mode=_get_mode(self.request))
        self.office_info_form = OfficeForm(instance=asset.office_info)
        self.part_info_form = BasePartForm(instance=asset.part_info)
        return super(EditPart, self).get(*args, **kwargs)

    @nested_commit_on_success
    def post(self, *args, **kwargs):
        asset = get_object_or_404(Asset, id=kwargs.get('asset_id'))
        self.asset_form = EditDeviceForm(
            self.request.POST, instance=asset, mode=_get_mode(self.request))
        self.office_info_form = OfficeForm(
            self.request.POST, self.request.FILES)
        self.part_info_form = BasePartForm(self.request.POST)
        if all((
            self.asset_form.is_valid(),
            self.office_info_form.is_valid(),
            self.part_info_form.is_valid()
        )):
            asset_data = self.asset_form.cleaned_data
            asset_data.update({'barcode': None})
            asset.__dict__.update(
                **asset_data)
            if not asset.office_info:
                office_info = OfficeInfo()
            else:
                office_info = asset.office_info
            office_info.__dict__.update(**self.office_info_form.cleaned_data)
            office_info.save()
            asset.office_info = office_info
            if not asset.part_info:
                part_info = PartInfo()
            else:
                part_info = asset.part_info
            part_info.__dict__.update(**self.part_info_form.cleaned_data)
            part_info.save()
            asset.part_info = part_info
            asset.save()
            return HttpResponseRedirect(_get_return_link(self.request))
        else:
            messages.error(self.request, _("Please correct the errors."))
        return super(EditPart, self).get(*args, **kwargs)


class BackOfficeEditPart(EditPart, BackOfficeMixin):
    sidebar_selected = None


class DataCenterEditPart(EditPart, DataCenterMixin):
    sidebar_selected = None


class BulkEdit(Base):
    template_name = 'assets/bulk_edit.html'

    def get_context_data(self, **kwargs):
        ret = super(BulkEdit, self).get_context_data(**kwargs)
        ret.update({
            'formset': self.asset_formset
        })
        return ret

    def get(self, *args, **kwargs):
        assets_count = Asset.objects.filter(
            pk__in=self.request.GET.getlist('assets', [])).count()
        if not assets_count:
            messages.warning(self.request, _("Nothing to edit."))
            return HttpResponseRedirect(_get_return_link(self.request))
        AssetFormSet = modelformset_factory(
            Asset,
            extra=0,
            exclude=(
                'created', 'modified', 'part_info',
                'office_info'
            )
        )
        self.asset_formset = AssetFormSet(
            queryset=Asset.objects.filter(
                pk__in=self.request.GET.getlist('assets', [])
            )
        )
        return super(BulkEdit, self).get(*args, **kwargs)

    @nested_commit_on_success
    def post(self, *args, **kwargs):
        AssetFormSet = modelformset_factory(
            Asset,
            extra=0,
            exclude=(
                'created', 'modified', 'part_info',
                'office_info'
            )
        )
        self.asset_formset = AssetFormSet(self.request.POST)
        if self.asset_formset.is_valid():
            device_infos = {}
            for item in self.asset_formset.cleaned_data:
                device_infos[item['id'].id] = item['id']
            instances = self.asset_formset.save(commit=False)
            for instance in instances:
                instance.modified_by = self.request.user.get_profile()
                instance.device_info = device_infos[instance.id].device_info
                instance.save()
            messages.success(self.request, _("Changes saved."))
            return HttpResponseRedirect(self.request.get_full_path())
        messages.error(self.request, _("Please correct the errors."))
        return super(BulkEdit, self).get(*args, **kwargs)


class BackOfficeBulkEdit(BulkEdit, BackOfficeMixin):
    sidebar_selected = None


class DataCenterBulkEdit(BulkEdit, DataCenterMixin):
    sidebar_selected = None

