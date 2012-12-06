# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from bob.menu import MenuItem, MenuHeader
from django.contrib import messages
from django.core.paginator import Paginator
from django.core.urlresolvers import resolve
from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponseRedirect, Http404
from django.forms.models import modelformset_factory
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _

from ralph.assets.forms import (
    AddDeviceForm, AddPartForm, EditDeviceForm,
    EditPartForm, BaseDeviceForm, OfficeForm,
    BasePartForm, BulkEditAssetForm, SearchAssetForm
)
from ralph.assets.models import (
    DeviceInfo, AssetSource, Asset, OfficeInfo, PartInfo,
)
from ralph.assets.models_assets import AssetType
from ralph.assets.models_history import AssetHistoryChange
from ralph.ui.views.common import Base, PaginationMixin


SAVE_PRIORITY = 200
HISTORY_PAGE_SIZE = 25
MAX_PAGE_SIZE = 65535
CONNECT_ASSET_WITH_DEVICE = settings.CONNECT_ASSET_WITH_DEVICE


class AssetsMixin(Base):
    template_name = "assets/base.html"

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


class AssetSearch(AssetsMixin, PaginationMixin):
    """The main-screen search form for all type of assets."""
    ROWS_PER_PAGE = 15

    def handle_search_data(self):
        search_fields = [
            'model', 'invoice_no', 'order_no',
            'provider', 'status', 'sn'
        ]
        # handle simple 'equals' search fields at once.
        all_q = Q()
        for field in search_fields:
            field_value = self.request.GET.get(field)
            if field_value:
                if field == 'model':
                    all_q &= Q(model__name__startswith=field_value)
                else:
                    q = Q(**{field: field_value})
                    all_q = all_q & q
        # now fields within ranges.
        buy_date_from = self.request.GET.get('buy_date_from')
        buy_date_to = self.request.GET.get('buy_date_to')
        if buy_date_from:
            all_q &= Q(buy_date__gte=buy_date_from)
        if buy_date_to:
            all_q &= Q(buy_date__lte=buy_date_to)
        self.paginate_query(self.get_all_items(all_q))

    def get_all_items(self, q_object):
        return Asset.objects.filter(q_object).order_by('id')

    def get_context_data(self, *args, **kwargs):
        ret = super(AssetSearch, self).get_context_data(*args, **kwargs)
        ret.update(
            super(AssetSearch, self).get_context_data_paginator(
                *args,
                **kwargs
            )
        )
        ret.update({
            'form': self.form,
            'header': self.header,
        })
        return ret

    def get(self, *args, **kwargs):
        self.form = SearchAssetForm(
            self.request.GET, mode=_get_mode(self.request)
        )
        self.handle_search_data()
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
    current_url = resolve(request.get_full_path())
    return current_url.url_name


def _get_return_link(request):
    return "/assets/%s/" % _get_mode(request)


@transaction.commit_on_success
def _create_device(creator_profile, asset_data, device_info_data, sn,
                   barcode=None):
    device_info = DeviceInfo(
        warehouse=device_info_data['warehouse'],
        size=device_info_data['size']
    )
    device_info.save(user=creator_profile.user)
    asset = Asset(
        device_info=device_info,
        sn=sn.strip(),
        created_by=creator_profile,
        **asset_data
    )
    if asset.type == AssetType.data_center.id and CONNECT_ASSET_WITH_DEVICE:
        asset.create_stock_device()
    if barcode:
        asset.barcode = barcode
    asset.save(user=creator_profile.user)


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
            creator_profile = self.request.user.get_profile()
            asset_data = {}
            for f_name, f_value in self.asset_form.cleaned_data.items():
                if f_name in ["barcode", "sn"]:
                    continue
                asset_data[f_name] = f_value
            asset_data['source'] = AssetSource.shipment
            serial_numbers = self.asset_form.cleaned_data['sn']
            barcodes = self.asset_form.cleaned_data['barcode']
            for sn, index in zip(serial_numbers, range(len(serial_numbers))):
                barcode = barcodes[index] if barcodes else None
                _create_device(
                    creator_profile, asset_data,
                    self.device_info_form.cleaned_data, sn, barcode
                )
            messages.success(self.request, _("Assets saved."))
            return HttpResponseRedirect(_get_return_link(self.request))
        else:
            messages.error(self.request, _("Please correct the errors."))
        return super(AddDevice, self).get(*args, **kwargs)


class BackOfficeAddDevice(AddDevice, BackOfficeMixin):
    sidebar_selected = 'add device'


class DataCenterAddDevice(AddDevice, DataCenterMixin):
    sidebar_selected = 'add device'


@transaction.commit_on_success
def _create_part(creator_profile, asset_data, part_info_data, sn):
    part_info = PartInfo(**part_info_data)
    part_info.save(user=creator_profile.user)
    asset = Asset(
        part_info=part_info,
        sn=sn.strip(),
        created_by=creator_profile,
        **asset_data
    )
    asset.save(user=creator_profile.user)


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
        mode = _get_mode(self.request)
        self.asset_form = AddPartForm(mode=mode)
        self.part_info_form = BasePartForm(mode=mode)
        return super(AddPart, self).get(*args, **kwargs)

    def post(self, *args, **kwargs):
        self.asset_form = AddPartForm(
            self.request.POST, mode=_get_mode(self.request))
        self.part_info_form = BasePartForm(
            self.request.POST, mode=_get_mode(self.request)
        )
        if self.asset_form.is_valid() and self.part_info_form.is_valid():
            creator_profile = self.request.user.get_profile()
            asset_data = self.asset_form.cleaned_data
            asset_data['source'] = AssetSource.shipment
            asset_data['barcode'] = None
            serial_numbers = self.asset_form.cleaned_data['sn']
            del asset_data['sn']
            for sn in serial_numbers:
                _create_part(
                    creator_profile, asset_data,
                    self.part_info_form.cleaned_data, sn
                )
            messages.success(self.request, _("Assets saved."))
            return HttpResponseRedirect(_get_return_link(self.request))
        else:
            messages.error(self.request, _("Please correct the errors."))
        return super(AddPart, self).get(*args, **kwargs)


class BackOfficeAddPart(AddPart, BackOfficeMixin):
    sidebar_selected = 'add part'


class DataCenterAddPart(AddPart, DataCenterMixin):
    sidebar_selected = 'add part'


@transaction.commit_on_success
def _update_asset(modifier_profile, asset, asset_updated_data):
    if ('barcode' not in asset_updated_data or
        not asset_updated_data['barcode']):
        asset_updated_data['barcode'] = None
    asset_updated_data.update({'modified_by': modifier_profile})
    asset.__dict__.update(**asset_updated_data)
    return asset


@transaction.commit_on_success
def _update_office_info(user, asset, office_info_data):
    if not asset.office_info:
        office_info = OfficeInfo()
    else:
        office_info = asset.office_info
    if office_info_data['attachment'] is None:
        del office_info_data['attachment']
    elif office_info_data['attachment'] is False:
        office_info_data['attachment'] = None
    office_info.__dict__.update(**office_info_data)
    office_info.save(user=user)
    asset.office_info = office_info
    return asset


@transaction.commit_on_success
def _update_device_info(user, asset, device_info_data):
    asset.device_info.__dict__.update(
        **device_info_data
    )
    asset.device_info.save(user=user)
    return asset


@transaction.commit_on_success
def _update_part_info(user, asset, part_info_data):
    if not asset.part_info:
        part_info = PartInfo()
    else:
        part_info = asset.part_info
    part_info.device = part_info_data.get('device')
    part_info.source_device = part_info_data.get('source_device')
    part_info.barcode_salvaged = part_info_data.get('barcode_salvaged')
    part_info.save(user=user)
    asset.part_info = part_info
    asset.part_info.save(user=user)
    return asset


class EditDevice(Base):
    template_name = 'assets/edit_device.html'

    def get_context_data(self, **kwargs):
        ret = super(EditDevice, self).get_context_data(**kwargs)
        status_history = AssetHistoryChange.objects.all().filter(
            asset=kwargs.get('asset_id'), field_name__exact='status'
        ).order_by('-date')
        ret.update({
            'asset_form': self.asset_form,
            'device_info_form': self.device_info_form,
            'office_info_form': self.office_info_form,
            'form_id': 'edit_device_asset_form',
            'edit_mode': True,
            'MaMaMastatus_history': status_history,
        })
        return ret

    def get(self, *args, **kwargs):
        asset = get_object_or_404(Asset, id=kwargs.get('asset_id'))
        if not asset.device_info:  # it isn't device asset
            raise Http404()
        self.asset_form = EditDeviceForm(
            instance=asset,
            mode=_get_mode(self.request)
        )
        self.device_info_form = BaseDeviceForm(instance=asset.device_info)
        self.office_info_form = OfficeForm(instance=asset.office_info)
        return super(EditDevice, self).get(*args, **kwargs)

    def post(self, *args, **kwargs):
        asset = get_object_or_404(Asset, id=kwargs.get('asset_id'))
        self.asset_form = EditDeviceForm(
            self.request.POST, instance=asset, mode=_get_mode(self.request)
        )
        self.device_info_form = BaseDeviceForm(self.request.POST)
        self.office_info_form = OfficeForm(
            self.request.POST, self.request.FILES
        )
        if all((
            self.asset_form.is_valid(),
            self.device_info_form.is_valid(),
            self.office_info_form.is_valid()
        )):
            modifier_profile = self.request.user.get_profile()
            asset = _update_asset(
                modifier_profile, asset, self.asset_form.cleaned_data
            )
            asset = _update_office_info(
                modifier_profile.user, asset,
                self.office_info_form.cleaned_data
            )
            asset = _update_device_info(
                modifier_profile.user, asset,
                self.device_info_form.cleaned_data
            )
            asset.save(user=self.request.user)
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
        status_history = AssetHistoryChange.objects.all().filter(
            asset=kwargs.get('asset_id'), field_name__exact='status'
        ).order_by('-date')
        ret.update({
            'asset_form': self.asset_form,
            'office_info_form': self.office_info_form,
            'part_info_form': self.part_info_form,
            'form_id': 'edit_part_form',
            'edit_mode': True,
            'status_history': status_history,
        })
        return ret

    def get(self, *args, **kwargs):
        asset = get_object_or_404(Asset, id=kwargs.get('asset_id'))
        if asset.device_info:  # it isn't part asset
            raise Http404()
        self.asset_form = EditPartForm(
            instance=asset,
            mode=_get_mode(self.request)
        )
        self.office_info_form = OfficeForm(instance=asset.office_info)
        self.part_info_form = BasePartForm(
            instance=asset.part_info, mode=_get_mode(self.request)
        )
        return super(EditPart, self).get(*args, **kwargs)

    def post(self, *args, **kwargs):
        asset = get_object_or_404(Asset, id=kwargs.get('asset_id'))
        self.asset_form = EditPartForm(
            self.request.POST, instance=asset, mode=_get_mode(self.request))
        self.office_info_form = OfficeForm(
            self.request.POST, self.request.FILES)
        self.part_info_form = BasePartForm(
            self.request.POST, mode=_get_mode(self.request)
        )
        if all((
            self.asset_form.is_valid(),
            self.office_info_form.is_valid(),
            self.part_info_form.is_valid()
        )):
            modifier_profile = self.request.user.get_profile()
            asset = _update_asset(
                modifier_profile, asset,
                self.asset_form.cleaned_data
            )
            asset = _update_office_info(
                modifier_profile.user, asset,
                self.office_info_form.cleaned_data
            )
            asset = _update_part_info(
                modifier_profile.user, asset,
                self.part_info_form.cleaned_data
            )
            asset.save(user=self.request.user)
            return HttpResponseRedirect(_get_return_link(self.request))
        else:
            messages.error(self.request, _("Please correct the errors."))
        return super(EditPart, self).get(*args, **kwargs)


class BackOfficeEditPart(EditPart, BackOfficeMixin):
    sidebar_selected = None


class DataCenterEditPart(EditPart, DataCenterMixin):
    sidebar_selected = None


class HistoryAsset(BackOfficeMixin):
    template_name = 'assets/history_asset.html'
    sidebar_selected = None

    def get_context_data(self, **kwargs):
        query_variable_name = 'history_page'
        ret = super(HistoryAsset, self).get_context_data(**kwargs)
        asset_id = kwargs.get('asset_id')
        asset = Asset.objects.get(id=asset_id)
        history = AssetHistoryChange.objects.filter(
            Q(asset_id=asset.id) |
            Q(device_info_id=getattr(asset.device_info, 'id', 0)) |
            Q(part_info_id=getattr(asset.part_info, 'id', 0)) |
            Q(office_info_id=getattr(asset.office_info, 'id', 0))
        ).order_by('-date')
        status = bool(self.request.GET.get('status', ''))
        if status:
            history = history.filter(field_name__exact='status')
        try:
            page = int(self.request.GET.get(query_variable_name, 1))
        except ValueError:
            page = 1
        if page == 0:
            page = 1
            page_size = MAX_PAGE_SIZE
        else:
            page_size = HISTORY_PAGE_SIZE
        history_page = Paginator(history, page_size).page(page)
        ret.update({
            'history': history,
            'history_page': history_page,
            'status': status,
            'query_variable_name': query_variable_name,
            'asset': asset,
        })
        return ret


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
            pk__in=self.request.GET.getlist('select')).exists()
        if not assets_count:
            messages.warning(self.request, _("Nothing to edit."))
            return HttpResponseRedirect(_get_return_link(self.request))
        AssetFormSet = modelformset_factory(
            Asset,
            form=BulkEditAssetForm,
            extra=0
        )
        self.asset_formset = AssetFormSet(
            queryset=Asset.objects.filter(
                pk__in=self.request.GET.getlist('select')
            )
        )
        return super(BulkEdit, self).get(*args, **kwargs)

    def post(self, *args, **kwargs):
        AssetFormSet = modelformset_factory(
            Asset,
            form=BulkEditAssetForm,
            extra=0
        )
        self.asset_formset = AssetFormSet(self.request.POST)
        if self.asset_formset.is_valid():
            with transaction.commit_on_success():
                instances = self.asset_formset.save(commit=False)
                for instance in instances:
                    instance.modified_by = self.request.user.get_profile()
                    instance.save()
            messages.success(self.request, _("Changes saved."))
            return HttpResponseRedirect(self.request.get_full_path())
        messages.error(self.request, _("Please correct the errors."))
        form_error = self.asset_formset.get_form_error()
        if form_error:
            messages.error(
                self.request,
                _("Please correct duplicated serial numbers or barcodes.")
            )
        return super(BulkEdit, self).get(*args, **kwargs)


class BackOfficeBulkEdit(BulkEdit, BackOfficeMixin):
    sidebar_selected = None


class DataCenterBulkEdit(BulkEdit, DataCenterMixin):
    sidebar_selected = None


class DeleteAsset(AssetsMixin):

    def post(self, *args, **kwargs):
        record_id = self.request.POST.get('record_id')
        try:
            self.asset = Asset.objects.get(
                pk=record_id
            )
        except Asset.DoesNotExist:
            messages.error(
                self.request, _("Selected asset doesn't exists.")
            )
            return HttpResponseRedirect(_get_return_link(self.request))
        else:
            if self.asset.type < AssetType.BO:
                self.back_to = '/assets/dc/'
            else:
                self.back_to = '/assets/back_office/'
            if self.asset.get_data_type() == 'device':
                PartInfo.objects.filter(
                    device=self.asset
                ).update(device=None)
            self.asset.deleted = True
            self.asset.save()
            return HttpResponseRedirect(self.back_to)
