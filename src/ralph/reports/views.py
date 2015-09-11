# -*- coding: utf-8 -*-

from django.db.models import Count
from django.http import Http404
from django.utils.translation import ugettext_lazy as _

from ralph.admin.mixins import RalphTemplateView
from ralph.assets.models.assets import Asset, AssetModel
from ralph.assets.models.choices import AssetStatus, ObjectModelType
from ralph.back_office.models import BackOfficeAsset
from ralph.data_center.models.physical import DataCenter, DataCenterAsset
from ralph.reports.base import ReportContainer


def get_desc(choices_class, key, default='------'):
    try:
        return choices_class.from_id(key) if key else default
    except ValueError:
        return 'Does not exist for key {}'.format(key)


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

        for item in queryset:
            parent = item['model__category__name'] or 'Without category'
            name = item['model__name']
            node, __ = self.report.add(
                name=name,
                parent=parent,
            )
            self.report.add(
                name=get_desc(AssetStatus, item['status']),
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
        for item in queryset:
            self.report.add(
                name=item['model__name'],
                count=item['num'],
                parent=get_desc(AssetStatus, item['status']),
                unique=False,
            )


class ReportViewBase(BaseReport, RalphTemplateView):

    reports = [
        CategoryModelReport,
        CategoryModelStatusReport,
        ManufacturerCategoryModelReport,
        StatusModelReport,
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

    def get_result(self, request, *args, **kwargs):
        report = self.get_report(request.resolver_match.url_name)
        return report.get_result(*args, **kwargs)

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


class ReportWithoutAllModeDetail(ReportDetail):
    """
    Turns off 'All' mode for report. Default mode is 'dc'.
    """
    default_mode = 'dc'

    @property
    def modes(self):
        return ReportDetail.modes[1:]
