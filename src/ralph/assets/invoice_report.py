# -*- coding: utf-8 -*-
import datetime
import json
import logging

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Sum
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext_lazy as _
from djmoney.money import Money

from ralph.admin.helpers import get_value_by_relation_path
from ralph.helpers import generate_pdf_response
from ralph.lib.external_services import ExternalService
from ralph.reports.models import Report, ReportTemplate

logger = logging.getLogger(__name__)


class ReportTemplateNotDefined(ValidationError):
    pass


class InvoiceReportMixin(object):
    actions = ["invoice_report"]

    _invoice_report_select_related = []
    _invoice_report_common_fields = [
        "invoice_no",
        "invoice_date",
        "provider",
        "price_currency",
        "property_of__name",
    ]
    _price_field = "price"
    _invoice_report_name = "invoice"
    _invoice_report_item_fields = []
    _invoice_report_empty_value = "-"
    _invoice_report_datetime_format = "%Y-%m-%d %H:%M:%S"

    def invoice_report(self, request, queryset):
        """
        Invoice report action
        """
        queryset = self._get_invoice_report_queryset(queryset)
        try:
            self._validate(queryset)
            return self._generate_invoice_report(request, queryset)
        except ValidationError as e:
            messages.error(request, e.message)

    invoice_report.short_description = _("Invoice report")

    def _validate(self, queryset):
        """
        Validate queryset items for equality of common fields in all items and
        check if all of the fields are filled.
        """
        values_distinct = queryset.values(
            *self._invoice_report_common_fields
        ).distinct()
        if values_distinct.count() != 1:
            raise ValidationError(self._get_non_unique_error(queryset))
        if not all(values_distinct[0].values()):
            raise ValidationError(
                "None of {} can't be empty".format(
                    ", ".join(self._invoice_report_common_fields)
                )
            )

    def _get_non_unique_error(self, queryset):
        """
        Generate error message when some of the field has more than one value.
        """
        non_unique = {}
        for field in self._invoice_report_common_fields:
            items = queryset.values(field).distinct()
            if items.count() != 1:
                if field == "invoice_date":
                    data = ", ".join(
                        item[field].strftime("%Y-%m-%d")
                        for item in items
                        if item[field]
                    )
                else:
                    data = ", ".join(item[field] for item in items if item[field])
                non_unique[field] = data
        non_unique_items = " ".join(
            ["{}: {}".format(key, value) for key, value in non_unique.items() if value]
        )
        return "{}: {}".format(
            _("Selected items have different"),
            non_unique_items,
        )

    def _generate_invoice_report(self, request, queryset):
        """
        Generate invoice report when data (queryset) is valid.
        """
        logger.info("Generating invoice report for model {}".format(queryset.model))
        data = self._get_report_data(request, queryset)
        content = self._get_pdf_content(data)
        file_name = "{}-{}.pdf".format(
            self._invoice_report_name,
            data["id"],
        )
        return generate_pdf_response(content, file_name)

    def _get_report_data(self, request, queryset):
        """
        Extract data in serializable form which will be passed to report
        service.
        """
        first_item = queryset[0]
        data = {
            "id": str(slugify(first_item.invoice_no)),
            "property_of_id": (
                first_item.property_of.id if first_item.property_of else None
            ),
            "model": queryset.model._meta.model_name,
            "base_info": {
                "invoice_no": first_item.invoice_no,
                "invoice_date": str(first_item.invoice_date),
                "provider": first_item.provider,
                "datetime": datetime.datetime.now().strftime(
                    self._invoice_report_datetime_format
                ),
                "property_of": first_item.property_of.name,
            },
            "items": list(map(self._parse_item, queryset)),
            "sum_price": str(
                queryset.aggregate(Sum(self._price_field)).get(
                    "{}__sum".format(self._price_field)
                )
            ),
        }
        logger.info("Invoice report data: {}".format(data))
        return data

    def _get_pdf_content(self, data):
        try:
            report = Report.objects.get(name=self._invoice_report_name)
            template = report.templates.filter(default=True).first()
        except (Report.DoesNotExist, ReportTemplate.DoesNotExist):
            raise ReportTemplateNotDefined(
                "Template for invoice report is not defined!"
            )
        logger.info(
            "Using report {} and template {}".format(
                report.name, template.template.path
            )
        )
        template_content = ""
        with open(template.template.path, "rb") as f:
            template_content = f.read()

        service_pdf = ExternalService("PDF")
        # Make sure data is JSON-serializable
        # Will throw otherwise
        data = json.loads(json.dumps(data))
        result = service_pdf.run(
            template=template_content,
            data=data,
        )
        return result

    def _get_invoice_report_queryset(self, queryset):
        """
        Allow to overwrite queryset which is used to generate invoice report.
        """
        return queryset.select_related(*self._invoice_report_select_related)

    def _parse_item(self, item):
        """
        Get item fields values (using django __ (double-underscore) convention
        for related fields).
        """
        result = {}
        for f in self._invoice_report_item_fields:
            val = get_value_by_relation_path(item, f)
            # when it's function - call it! usefull for Choices
            # (get_<field_name>_display)
            if callable(val):
                val = val()
            elif isinstance(val, datetime.datetime):
                val = val.strftime(self._invoice_report_datetime_format)
            elif isinstance(val, Money):
                val_currency = "{}_currency".format(self._price_field)
                result[val_currency] = (
                    str(val.currency)
                    if val.currency
                    else self._invoice_report_empty_value
                )
                val = val.amount
            result[f] = str(val) if val else self._invoice_report_empty_value

        return result


class AssetInvoiceReportMixin(InvoiceReportMixin):
    _invoice_report_empty_value = None

    _invoice_report_select_related = ["model", "model__manufacturer", "property_of"]
    _invoice_report_item_fields = [
        "model",
        "barcode",
        "niw",
        "sn",
        "price",
        "property_of",
        "created",
        "model__get_type_display",
        "start_usage",
    ]
