# -*- coding: utf-8 -*-
import logging

import tablib
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db.models import Count, Prefetch
from django.http import HttpResponse
from django.urls import reverse
from django.utils.encoding import smart_str
from django.utils.translation import ugettext_lazy as _

from ralph.admin.helpers import getattr_dunder
from ralph.admin.mixins import RalphTemplateView
from ralph.assets.models.assets import Asset, AssetModel
from ralph.assets.models.choices import ObjectModelType
from ralph.back_office.models import BackOfficeAsset
from ralph.data_center.models.physical import DataCenter, DataCenterAsset
from ralph.licences.models import BaseObjectLicence, Licence, LicenceUser
from ralph.operations.models import Failure, OperationType
from ralph.reports.base import ReportContainer
from ralph.supports.models import BaseObjectsSupport

logger = logging.getLogger(__name__)


def get_choice_name(choices_class, key, default="------"):
    """
    Return raw name of choice for given key.
    """
    try:
        return choices_class.from_id(key) if key else default
    except ValueError:
        logger.error("Choice not found for key %s", key)
        return "Does not exist for key {}".format(key)


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
        response = HttpResponse(data.csv, content_type="text/csv;charset=utf-8")
        response["Content-Disposition"] = "attachment;filename={}".format(self.filename)
        return response


class ReportDetail(RalphTemplateView):
    template_name = "reports/report_detail.html"
    default_mode = "all"
    with_modes = True
    with_datacenters = False
    with_counter = True
    links = False
    modes = [
        {
            "name": "all",
            "verbose_name": _("All"),
            "model": Asset,
        },
        {
            "name": "dc",
            "verbose_name": _("Only data center"),
            "model": DataCenterAsset,
        },
        {
            "name": "back_office",
            "verbose_name": _("Only back office"),
            "model": BackOfficeAsset,
        },
    ]

    def __init__(self):
        self.report = ReportContainer()

    def execute(self, model, dc=None):
        self.dc = dc
        self.prepare(model, dc=dc)
        for item in self.report.leaves:
            item.update_count()
        return self.report.roots

    def prepare(self, model, dc):
        raise NotImplementedError()

    def is_async(self, request):
        return False

    @property
    def datacenters(self):
        datacenters = [
            {
                "name": "all",
                "verbose_name": "All",
                "id": "all",
            },
        ]
        return datacenters + [
            {
                "name": dc.name.lower(),
                "verbose_name": dc.name,
                "id": dc.id,
            }
            for dc in DataCenter.objects.all()
        ]

    def get_model(self, asset_type="all"):
        for mode in self.modes:
            if mode["name"] == asset_type:
                return mode["model"]
        return None

    @property
    def active_sidebar_item(self):
        return self.name

    def get_template_names(self, *args, **kwargs):
        return [self.template_name]

    def get_result(self, request, model, *args, **kwargs):
        return list(self.prepare(model, *args, **kwargs))

    def dispatch(self, request, *args, **kwargs):
        try:
            self.dc = DataCenter.objects.get(id=request.GET.get("dc", None))
        except (DataCenter.DoesNotExist, ValueError):
            self.dc = None
        self.slug = request.resolver_match.url_name
        self.asset_type = request.GET.get("asset_type") or self.default_mode
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data.update(
            {
                "report": self,
                "subsection": self.name,
                "result": self.execute(
                    self.get_model(self.asset_type),
                    self.dc,
                ),
                "cache_key": (
                    self.asset_type
                    + (str(self.dc.id) if self.dc else "all")
                    + self.slug
                ),
                "modes": self.modes,
                "mode": self.asset_type,
                "datacenters": self.datacenters,
                "slug": self.slug,
                "dc": self.dc.id if self.dc else "all",
            }
        )
        return context_data

    def get(self, request, *args, **kwargs):
        if request.GET.get("csv"):
            model = self.get_model(self.asset_type)
            return self.get_response(request, self.get_result(request, model))
        return super().get(request, *args, **kwargs)


class ReportWithoutAllModeDetail(object):
    """
    Turns off 'All' mode for report. Default mode is 'dc'.
    """

    default_mode = "dc"

    @property
    def modes(self):
        return ReportDetail.modes[1:]


class CategoryModelReport(ReportDetail):
    name = _("Category - model")
    description = _("Number of assets in each model category.")

    def prepare(self, model, *args, **kwargs):
        queryset = model.objects
        queryset = (
            queryset.select_related("model", "category")
            .values(
                "model__category__name",
                "model__name",
            )
            .annotate(num=Count("model"))
            .order_by("model__category__name")
        )

        for item in queryset:
            cat = item["model__category__name"] or "None"
            self.report.add(
                name=item["model__name"],
                parent=cat,
                count=item["num"],
            )


class CategoryModelStatusReport(ReportWithoutAllModeDetail, ReportDetail):
    name = _("Category - model - status")
    description = _("Number of assets in each status in the model category.")

    def prepare(self, model, *args, **kwargs):
        queryset = model.objects
        queryset = (
            queryset.select_related("model", "category")
            .values(
                "model__category__name",
                "model__name",
                "status",
            )
            .annotate(num=Count("status"))
            .order_by("model__category__name")
        )
        # get status class dynamically for BO/DC Asset
        status_class = model._meta.get_field("status").choices.__class__
        for item in queryset:
            parent = item["model__category__name"] or "Without category"
            name = item["model__name"]
            node, __ = self.report.add(
                name=name,
                parent=parent,
            )
            self.report.add(
                name=get_choice_name(status_class, item["status"]),
                parent=node,
                count=item["num"],
                unique=False,
            )


class ManufacturerCategoryModelReport(ReportDetail):
    name = _("Manufactured - category - model")
    description = _("Number of assets in each manufacturer.")

    def prepare(self, model, *args, **kwargs):
        queryset = AssetModel.objects
        if model._meta.object_name == "BackOfficeAsset":
            queryset = queryset.filter(type=ObjectModelType.back_office)
        if model._meta.object_name == "DataCenterAsset":
            queryset = queryset.filter(type=ObjectModelType.data_center)

        queryset = (
            queryset.select_related(
                "manufacturer",
                "category",
            )
            .values(
                "manufacturer__name",
                "category__name",
                "name",
            )
            .annotate(num=Count("assets"))
            .order_by("manufacturer__name")
        )

        for item in queryset:
            manufacturer = item["manufacturer__name"] or "Without manufacturer"
            node, __ = self.report.add(
                name=item["category__name"],
                parent=manufacturer,
            )
            self.report.add(
                name=item["name"],
                parent=node,
                count=item["num"],
            )


class StatusModelReport(ReportWithoutAllModeDetail, ReportDetail):
    with_datacenters = True
    name = _("Status - model")
    description = _("Number of assets in each the asset status.")

    def prepare(self, model, dc=None):
        queryset = model.objects
        if dc:
            queryset = queryset.filter(rack__server_room__data_center=dc)

        queryset = queryset.values(
            "status",
            "model__name",
        ).annotate(num=Count("model"))
        # get status class dynamically for BO/DC Asset
        status_class = model._meta.get_field("status").choices.__class__
        for item in queryset:
            self.report.add(
                name=item["model__name"],
                count=item["num"],
                parent=get_choice_name(status_class, item["status"]),
                unique=False,
            )


class BaseRelationsReport(ReportWithoutAllModeDetail, ReportDetail, CSVReportMixin):
    template_name = "reports/report_relations.html"
    with_modes = True
    links = False


class AssetRelationsReport(BaseRelationsReport):
    name = _("Asset - relations")
    description = _("Asset list of information about the user, owner, model.")
    filename = "asset_relations.csv"
    extra_headers = ["tags"]
    dc_headers = [
        "id",
        "niw",
        "barcode",
        "sn",
        "model__category__name",
        "model__manufacturer__name",
        "model__name",
        "status",
        "service_env__service__name",
        "invoice_date",
        "invoice_no",
        "hostname",
        "rack",
    ]
    dc_select_related = [
        "model",
        "model__category",
        "service_env",
        "service_env__service",
        "model__manufacturer",
        "rack",
        "rack__server_room",
        "rack__server_room__data_center",
    ]
    bo_headers = [
        "id",
        "niw",
        "barcode",
        "sn",
        "model__category__name",
        "model__manufacturer__name",
        "model__name",
        "price__amount",
        "price__currency",
        "remarks",
        "service_env",
        "user__username",
        "user__first_name",
        "user__last_name",
        "owner__username",
        "owner__first_name",
        "owner__last_name",
        "owner__company",
        "owner__segment",
        "status",
        "office_infrastructure__name",
        "property_of",
        "warehouse__name",
        "invoice_date",
        "invoice_no",
        "region__name",
        "hostname",
        "depreciation_rate",
        "buyout_date",
    ]
    bo_select_related = [
        "model",
        "model__category",
        "office_infrastructure",
        "warehouse",
        "user",
        "owner",
        "model__manufacturer",
        "region",
        "property_of",
    ]

    def prepare(self, model, *args, **kwargs):
        queryset = model.objects.prefetch_related("tags")
        headers = self.bo_headers
        select_related = self.bo_select_related
        if model._meta.object_name == "DataCenterAsset":
            headers = self.dc_headers
            select_related = self.dc_select_related

        yield headers + self.extra_headers
        for asset in queryset.select_related(*select_related):
            row = [str(getattr_dunder(asset, column)) for column in headers]
            row += self.get_extra_columns(asset)
            yield row

    def get_extra_columns(self, obj):
        """
        Call extra methods for object.
        """
        return [self._get_tags(obj)]

    def _get_tags(self, obj):
        """
        Return comma-separated list of tags for object
        """
        return ",".join(sorted(map(str, obj.tags.all())))


class AssetSupportsReport(BaseRelationsReport):
    name = _("Asset - supports")
    description = _("Assets with assigned supports")
    filename = "asset_supports.csv"
    extra_headers = ["supprt_price_per_object", "attachments"]
    # TODO(mkurek): allow for fields aliases in headers (ex. use tuple with
    # (field_name, header_name))
    # TODO(mkurek): unify these reports
    dc_headers = [
        "baseobject__id",
        "baseobject__asset__barcode",
        "baseobject__asset__sn",
        "baseobject__asset__datacenterasset__hostname",
        "baseobject__service_env__service__name",
        "baseobject__asset__invoice_date",
        "baseobject__asset__invoice_no",
        "baseobject__asset__property_of",
        "support__name",
        "support__contract_id",
        "support__date_to",
        "support__date_from",
        "support__invoice_date",
        "support__price__amount",
        "support__price__currency",
    ]
    dc_select_related = [
        "baseobject__asset__datacenterasset",
    ]
    bo_headers = [
        "baseobject__id",
        "baseobject__asset__barcode",
        "baseobject__asset__sn",
        "baseobject__asset__invoice_date",
        "baseobject__asset__invoice_no",
        "baseobject__asset__property_of",
        "support__name",
        "support__contract_id",
        "support__date_to",
        "support__date_from",
        "support__invoice_date",
        "support__price__amount",
        "support__price__currency",
    ]
    bo_select_related = [
        "baseobject__asset__backofficeasset",
    ]

    def prepare(self, model, *args, **kwargs):
        queryset = BaseObjectsSupport.objects.select_related(
            "support",
            "baseobject__asset__property_of",
            "baseobject__service_env__service",
        ).prefetch_related(
            # AttachmentItem is attached to BaseObject (by content type),
            # so we need to prefetch attachments through base object of support
            "support__baseobject_ptr__attachments__attachment",
            "support__baseobjectssupport_set",
        )
        headers = []
        select_related = []
        if model._meta.object_name == "DataCenterAsset":
            headers = self.dc_headers
            select_related = self.dc_select_related
            queryset = queryset.filter(
                baseobject__content_type=ContentType.objects.get_for_model(
                    DataCenterAsset
                )
            )
        elif model._meta.object_name == "BackOfficeAsset":
            headers = self.bo_headers
            select_related = self.bo_select_related
            queryset = queryset.filter(
                baseobject__content_type=ContentType.objects.get_for_model(
                    BackOfficeAsset
                )
            )

        yield headers + self.extra_headers
        for bos in queryset.select_related(*select_related):
            row = [str(getattr_dunder(bos, column)) for column in headers]
            row += self.get_extra_columns(bos)
            yield row

    def get_extra_columns(self, obj):
        """
        Call extra methods for object.
        """
        return [
            self._get_supprt_price_per_object(obj.support),
            self._get_attachment_urls(obj.support.baseobject_ptr),
        ]

    def _get_supprt_price_per_object(self, obj):
        """
        Return support price per base objects.
        """
        # Intentional used len(), so that django for the count()
        # performs additional SQL query.
        bo_count = len(obj.baseobjectssupport_set.all())
        if bo_count > 0 and obj.price and obj.price.amount > 0:
            return "{0:.2f}".format(obj.price.amount / bo_count)
        return "0.00"

    def _get_attachment_urls(self, obj):
        """
        Return semicolon-separated list of attachments for object
        """
        return "; ".join(
            [
                "{}{}".format(
                    settings.RALPH_INSTANCE,
                    reverse(
                        "serve_attachment",
                        kwargs={
                            "id": attachment_item.attachment.id,
                            "filename": attachment_item.attachment.original_filename,
                        },
                    ),
                )
                for attachment_item in obj.attachments.all()
            ]
        )


class LicenceRelationsReport(BaseRelationsReport):
    name = _("Licence - relations")
    filename = "licence_relations.csv"
    description = _("List of licenses assigned to assets and users.")

    licences_headers = [
        "niw",
        "software",
        "number_bought",
        "price__amount",
        "price__currency",
        "invoice_date",
        "invoice_no",
        "region",
    ]
    licences_asset_headers = [
        "id",
        "asset__barcode",
        "asset__niw",
        "asset__backofficeasset__user__username",
        "asset__backofficeasset__user__first_name",
        "asset__backofficeasset__user__last_name",
        "asset__backofficeasset__owner__username",
        "asset__backofficeasset__owner__first_name",
        "asset__backofficeasset__owner__last_name",
        "asset__backofficeasset__region__name",
    ]
    licences_users_headers = ["user__username", "user__first_name", "user__last_name"]

    def prepare(self, model, *args, **kwargs):
        queryset = Licence.objects.select_related("region", "software")
        asset_related = [None]
        if model._meta.object_name == "BackOfficeAsset":
            queryset = queryset.filter(
                software__asset_type__in=(
                    ObjectModelType.back_office,
                    ObjectModelType.all,
                )
            )
            asset_related = [
                "base_object__asset",
                "base_object__asset__backofficeasset",
                "base_object__asset__backofficeasset__user",
                "base_object__asset__backofficeasset__owner",
                "base_object__asset__backofficeasset__region",
            ]
        if model._meta.object_name == "DataCenterAsset":
            queryset = queryset.filter(software__asset_type=ObjectModelType.data_center)
            asset_related = [
                "base_object__asset",
                "base_object__asset__backofficeasset",
            ]

        fill_empty_assets = [""] * len(self.licences_asset_headers)
        fill_empty_licences = [""] * len(self.licences_users_headers)

        headers = (
            self.licences_headers
            + self.licences_asset_headers
            + self.licences_users_headers
            + ["single_cost"]
        )
        yield headers

        queryset = queryset.select_related("software").prefetch_related(
            Prefetch(
                "licenceuser_set", queryset=LicenceUser.objects.select_related("user")
            ),
            Prefetch(
                "baseobjectlicence_set",
                queryset=BaseObjectLicence.objects.select_related(*asset_related),
            ),
        )

        for licence in queryset:
            row = [
                smart_str(getattr_dunder(licence, column))
                for column in self.licences_headers
            ]
            base_row = row

            row = row + fill_empty_assets + fill_empty_licences + [""]
            yield row
            if licence.number_bought > 0 and licence.price:
                single_licence_cost = str(licence.price.amount / licence.number_bought)
            else:
                single_licence_cost = ""

            for asset in licence.baseobjectlicence_set.all():
                row = [
                    smart_str(
                        getattr_dunder(asset.base_object, column),
                    )
                    for column in self.licences_asset_headers
                ]
                yield base_row + row + fill_empty_licences + [single_licence_cost]
            for user in licence.licenceuser_set.all():
                row = [
                    smart_str(getattr_dunder(user, column))
                    for column in self.licences_users_headers
                ]
                yield base_row + fill_empty_assets + row + [single_licence_cost]


class FailureReport(ReportWithoutAllModeDetail, ReportDetail):
    with_datacenters = True
    name = _("Failures")
    description = _("Failure types for each manufacturer.")

    def prepare(self, model, dc=None):
        queryset = model._default_manager
        if dc:
            queryset = queryset.filter(rack__server_room__data_center=dc)
        operation_types = OperationType.objects.get(
            pk=OperationType.choices.failure
        ).get_descendants(include_self=True)
        failures = (
            Failure.base_objects.through.objects.filter(
                baseobject__in=queryset.all(), operation__type__in=operation_types
            )
            .values(
                "baseobject__asset__model__manufacturer__name", "operation__type__name"
            )
            .annotate(
                count=Count("id"),
            )
        )
        for item in failures:
            parent = item["baseobject__asset__model__manufacturer__name"] or "None"
            self.report.add(
                name=item["operation__type__name"],
                count=item["count"],
                parent=parent,
                unique=False,
            )
