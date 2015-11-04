# -*- coding: utf-8 -*-
import logging

import tablib
from django.contrib.contenttypes.models import ContentType
from django.db.models import Count
from django.http import Http404, HttpResponse
from django.utils.encoding import smart_str
from django.utils.translation import ugettext_lazy as _

from ralph.admin.helpers import getattr_dunder
from ralph.admin.mixins import RalphTemplateView
from ralph.assets.models.assets import Asset, AssetModel
from ralph.assets.models.choices import ObjectModelType
from ralph.back_office.models import BackOfficeAsset
from ralph.data_center.models.physical import DataCenter, DataCenterAsset
from ralph.licences.models import Licence
from ralph.reports.base import ReportContainer

logger = logging.getLogger(__name__)


def get_choice_name(choices_class, key, default='------'):
    """
    Return raw name of choice for given key.
    """
    try:
        return choices_class.from_id(key) if key else default
    except ValueError:
        logger.error('Choice not found for key {}'.format(key))
        return 'Does not exist for key {}'.format(key)


class CSVReportMixin(object):
    """CSV report mixin.

    Adding the required method get_resposne
    """

    def get_response(self, request, result):
        """Get django response method.

        Args:
            request: Django request object
            result: data list

        Returns:
            Django response object
        """
        data = tablib.Dataset(*result[1:], headers=result[0])
        response = HttpResponse(
            data.csv,
            content_type='text/csv;charset=utf-8'
        )
        response['Content-Disposition'] = 'attachment;filename={}'.format(
            self.filename
        )
        return response


class BaseReport(object):
    """Each report must inherit from this class."""
    with_modes = True
    with_datacenters = False
    with_counter = True
    links = False
    template_name = None

    def __init__(self):
        self.report = ReportContainer()

    def execute(self, model, dc=None):
        self.dc = dc
        self.prepare(model, dc=dc)
        for item in self.report.leaves:
            item.update_count()
        return self.report.roots

    def prepare(self, model, dc):
        raise NotImplemented()

    def is_async(self, request):
        return False


class CategoryModelReport(BaseReport):

    slug = 'category_model_report'
    name = _('Category - model')
    description = _('Number of assets in each model category.')

    def prepare(self, model, *args, **kwargs):
        queryset = model.objects
        queryset = queryset.select_related('model', 'category').values(
            'model__category__name',
            'model__name',
        ).annotate(
            num=Count('model')
        ).order_by('model__category__name')

        for item in queryset:
            cat = item['model__category__name'] or 'None'
            self.report.add(
                name=item['model__name'],
                parent=cat,
                count=item['num'],
            )


class CategoryModelStatusReport(BaseReport):

    slug = 'category_model__status_report'
    name = _('Category - model - status')
    description = _('Number of assets in each status in the model category.')

    def prepare(self, model, *args, **kwargs):
        queryset = model.objects
        queryset = queryset.select_related('model', 'category').values(
            'model__category__name',
            'model__name',
            'status',
        ).annotate(
            num=Count('status')
        ).order_by('model__category__name')
        # get status class dynamically for BO/DC Asset
        status_class = model._meta.get_field('status').choices.__class__
        for item in queryset:
            parent = item['model__category__name'] or 'Without category'
            name = item['model__name']
            node, __ = self.report.add(
                name=name,
                parent=parent,
            )
            self.report.add(
                name=get_choice_name(status_class, item['status']),
                parent=node,
                count=item['num'],
                unique=False
            )


class ManufacturerCategoryModelReport(BaseReport):

    slug = 'manufactured_category_model_report'
    name = _('Manufactured - category - model')
    description = _('Number of assets in each manufacturer.')

    def prepare(self, model, *args, **kwargs):
        queryset = AssetModel.objects
        if model._meta.object_name == 'BackOfficeAsset':
            queryset = queryset.filter(type=ObjectModelType.back_office)
        if model._meta.object_name == 'DataCenterAsset':
            queryset = queryset.filter(type=ObjectModelType.data_center)

        queryset = queryset.select_related(
            'manufacturer',
            'category',
        ).values(
            'manufacturer__name',
            'category__name',
            'name',
        ).annotate(
            num=Count('assets')
        ).order_by('manufacturer__name')

        for item in queryset:
            manufacturer = item['manufacturer__name'] or 'Without manufacturer'
            node, __ = self.report.add(
                name=item['category__name'],
                parent=manufacturer,
            )
            self.report.add(
                name=item['name'],
                parent=node,
                count=item['num'],
            )


class StatusModelReport(BaseReport):

    with_datacenters = True
    slug = 'status_model_report'
    name = _('Status - model')
    description = _('Number of assets in each the asset status.')

    def prepare(self, model, dc=None):
        queryset = model.objects
        if dc:
            queryset = queryset.filter(rack__server_room__data_center=dc)

        queryset = queryset.values(
            'status',
            'model__name',
        ).annotate(
            num=Count('model')
        )
        # get status class dynamically for BO/DC Asset
        status_class = model._meta.get_field('status').choices.__class__
        for item in queryset:
            self.report.add(
                name=item['model__name'],
                count=item['num'],
                parent=get_choice_name(status_class, item['status']),
                unique=False,
            )


class BaseRelationsReport(BaseReport, CSVReportMixin):

    template_name = 'reports/report_relations.html'
    with_modes = True
    links = False


class AssetRelationsReport(BaseRelationsReport):
    slug = 'asset-relations'
    name = _('Asset - relations')
    description = _('Asset list of information about the user, owner, model.')
    filename = 'asset_relations.csv'
    dc_headers = [
        'id', 'niw', 'barcode', 'sn', 'model__category__name',
        'model__manufacturer__name', 'status', 'service_env__service__name',
        'invoice_date', 'invoice_no', 'hostname'
    ]
    dc_select_related = [
        'model', 'model__category', 'service_env', 'service_env__service'
    ]
    bo_headers = [
        'id', 'niw', 'barcode', 'sn', 'model__category__name',
        'model__manufacturer__name', 'model__name', 'user__username',
        'user__first_name', 'user__last_name', 'owner__username',
        'owner__first_name', 'owner__last_name', 'owner__company',
        'owner__segment', 'status', 'service_env__service__name',
        'property_of', 'warehouse__name', 'invoice_date', 'invoice_no',
        'region__name', 'hostname'
    ]
    bo_select_related = [
        'model', 'model__category', 'service_env', 'service_env__service',
        'warehouse', 'user', 'owner'
    ]

    def prepare(self, model, *args, **kwargs):
        queryset = model.objects.all()
        headers = self.bo_headers
        select_related = self.bo_select_related
        if model._meta.object_name == 'DataCenterAsset':
            headers = self.dc_headers
            select_related = self.dc_select_related

        yield headers
        for asset in queryset.select_related(*select_related).values(*headers):
            row = [asset.get(column) for column in headers]
            yield row


class LicenceRelationsReport(BaseRelationsReport):
    slug = 'licence-relations'
    name = _('Licence - relations')
    filename = 'licence_relations.csv'
    description = _('List of licenses assigned to assets and users.')

    licences_headers = [
        'niw', 'software', 'number_bought', 'price', 'invoice_date',
        'invoice_no'
    ]
    licecses_asset_headers = [
        'id', 'asset__barcode', 'asset__niw', 'asset__user__username',
        'asset__user__first_name', 'asset__user__last_name',
        'asset__owner__username', 'asset__owner__first_name',
        'asset__owner__last_name', 'region__name'
    ]
    licenses_users_headers = ['username', 'first_name', 'last_name']

    def prepare(self, model, *args, **kwargs):
        queryset = Licence.objects.all()
        if model._meta.object_name == 'BackOfficeAsset':
            queryset = queryset.filter(
                base_objects__content_type=ContentType.objects.get_for_model(
                    BackOfficeAsset
                )
            )
        if model._meta.object_name == 'DataCenterAsset':
            queryset = queryset.filter(
                base_objects__content_type=ContentType.objects.get_for_model(
                    DataCenterAsset
                )
            )

        fill_empty_assets = [''] * len(self.licecses_asset_headers)
        fill_empty_licences = [''] * len(self.licenses_users_headers)

        headers = self.licences_headers + self.licecses_asset_headers + \
            self.licenses_users_headers + ['single_cost']

        yield headers

        queryset = queryset.select_related('software')

        for licence in queryset:
            row = [
                smart_str(getattr_dunder(licence, column))
                for column in self.licences_headers
            ]
            base_row = row

            row = row + fill_empty_assets + fill_empty_licences + ['']
            yield row
            if licence.number_bought > 0 and licence.price:
                single_licence_cost = str(
                    licence.price / licence.number_bought
                )
            else:
                single_licence_cost = ''

            asset_related = [None]
            if model._meta.object_name == 'BackOfficeAsset':
                asset_related = [
                    'asset_ptr', 'asset_ptr__user', 'asset_ptr__owner',
                    'asset_ptr__region'
                ]
            for asset in licence.base_objects.all().select_related(
                *asset_related
            ):
                row = [
                    smart_str(
                        getattr_dunder(asset, column),
                    ) for column in self.licecses_asset_headers
                ]
                yield base_row + row + fill_empty_licences + [
                    single_licence_cost
                ]
            for user in licence.users.all().values(
                *self.licenses_users_headers
            ):
                row = [
                    smart_str(user.get(column))
                    for column in self.licenses_users_headers
                ]
                yield base_row + fill_empty_assets + row + [
                    single_licence_cost
                ]


class ReportViewBase(BaseReport, RalphTemplateView):

    reports = [
        CategoryModelReport,
        CategoryModelStatusReport,
        ManufacturerCategoryModelReport,
        StatusModelReport,
        AssetRelationsReport,
        LicenceRelationsReport
    ]

    modes = [
        {
            'name': 'all',
            'verbose_name': _('All'),
            'model': Asset,
        },
        {
            'name': 'dc',
            'verbose_name': _('Only data center'),
            'model': DataCenterAsset,
        },
        {
            'name': 'back_office',
            'verbose_name': _('Only back office'),
            'model': BackOfficeAsset,
        },
    ]

    @property
    def datacenters(self):
        datacenters = [
            {
                'name': 'all',
                'verbose_name': 'All',
                'id': 'all',
            },
        ]
        return datacenters + [
            {
                'name': dc.name.lower(),
                'verbose_name': dc.name,
                'id': dc.id,
            } for dc in DataCenter.objects.all()
        ]

    def get_model(self, asset_type='all'):
        for mode in self.modes:
            if mode['name'] == asset_type:
                return mode['model']
        return None


class ReportDetail(ReportViewBase):

    template_name = 'reports/report_detail.html'
    default_mode = 'all'

    @property
    def active_sidebar_item(self):
        return self.report.name

    def get_report(self, slug):
        for report in self.reports:
            if report.slug == slug:
                return report()
        return None

    def get_template_names(self, *args, **kwargs):
        return [self.report.template_name or self.template_name]

    def is_async(self, request, *args, **kwargs):
        return self.report.is_async(request)

    def get_result(self, request, model, *args, **kwargs):
        report = self.get_report(request.resolver_match.url_name)
        return list(report.prepare(model, *args, **kwargs))

    def get_response(self, request, result):
        return self.report.get_response(request, result)

    def dispatch(self, request, *args, **kwargs):
        try:
            self.dc = DataCenter.objects.get(
                id=request.GET.get('dc', None)
            )
        except (DataCenter.DoesNotExist, ValueError):
            self.dc = None
        self.slug = request.resolver_match.url_name
        self.asset_type = request.GET.get('asset_type') or self.default_mode
        self.report = self.get_report(self.slug)
        if not self.report:
            raise Http404
        return super(ReportDetail, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data.update({
            'report': self.report,
            'subsection': self.report.name,
            'result': self.report.execute(
                self.get_model(self.asset_type),
                self.dc,
            ),
            'cache_key': (
                self.asset_type +
                (str(self.dc.id) if self.dc else 'all') +
                self.slug
            ),
            'modes': self.modes,
            'mode': self.asset_type,
            'datacenters': self.datacenters,
            'slug': self.slug,
            'dc': self.dc.id if self.dc else 'all',
        })
        return context_data

    def get(self, request, *args, **kwargs):
        if request.GET.get('csv'):
            model = self.get_model(self.asset_type)
            return self.get_response(request, self.get_result(request, model))
        return super().get(request, *args, **kwargs)


class ReportWithoutAllModeDetail(ReportDetail):
    """
    Turns off 'All' mode for report. Default mode is 'dc'.
    """
    default_mode = 'dc'

    @property
    def modes(self):
        return ReportDetail.modes[1:]
