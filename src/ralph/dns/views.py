# -*- coding: utf-8 -*-
import logging
from enum import Enum

from django.conf import settings
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _

from ralph.admin.views.extra import RalphDetailView
from ralph.dns.dnsaas import DNSaaS
from ralph.dns.forms import DNSRecordForm, RecordType

logger = logging.getLogger(__name__)


class DNSaaSIntegrationNotEnabledError(Exception):
    pass


class DnsaasErrorReasonToFieldNameEnum(Enum):
    NAME = "name"
    TYPE = "type"
    CONTENT = "content"
    _DEFAULT = None


def add_errors(form, errors):
    """
    Set `errors` on `form`.

    form: Django form, form.Form
    errors: list of errors from DNSAAS
    """
    for error in errors.get("errors", []):
        reason = error.get("reason", "_DEFAULT")
        try:
            field_name = DnsaasErrorReasonToFieldNameEnum[reason].value
        except KeyError:
            field_name = DnsaasErrorReasonToFieldNameEnum._DEFAULT.value

        field_error = error.get("comment", "Unknown error")
        form.add_error(field_name, field_error)


class DNSView(RalphDetailView):
    icon = "chain-broken"
    name = "dns_edit"
    label = "DNS"
    url_name = "dns_edit"
    template_name = "dns/dns_edit.html"

    def __init__(self, *args, **kwargs):
        if not settings.ENABLE_DNSAAS_INTEGRATION:
            raise DNSaaSIntegrationNotEnabledError()
        self.dnsaas = DNSaaS()
        return super().__init__(*args, **kwargs)

    def get_forms(self):
        forms = []
        ipaddresses = self.object.ipaddresses.all().values_list("address", flat=True)
        if not ipaddresses:
            # If ipaddresses is empty return empty form list because we can not
            # identify the records do not have any IP address
            return forms

        initial = self.dnsaas.get_dns_records(ipaddresses)
        for item in initial:
            forms.append(DNSRecordForm(item))

        if initial and initial[0]["type"] == RecordType.a.id:
            # from API "A" record is always first
            empty_form = DNSRecordForm(initial={"name": initial[0]["name"]})
        else:
            empty_form = DNSRecordForm()

        forms.append(empty_form)
        return forms

    def get(self, request, *args, **kwargs):
        if "forms" not in kwargs:
            kwargs["forms"] = self.get_forms()
        return super().get(request, *kwargs, **kwargs)

    def post(self, request, *args, **kwargs):
        forms = self.get_forms()
        posted_form = DNSRecordForm(request.POST)
        # Find form which request's data belongs to
        for i, form in enumerate(forms):
            if str(form.data.get("pk", "")) == str(posted_form.data.get("pk", "")):
                forms[i] = posted_form
                break

        if posted_form.is_valid():
            if posted_form.data.get("delete"):
                errors = self.dnsaas.delete_dns_record(form.data["pk"])
                if not errors:
                    messages.success(request, _("DNS record has been deleted."))
            elif posted_form.cleaned_data.get("pk"):
                errors = self.dnsaas.update_dns_record(posted_form.cleaned_data)
                if not errors:
                    messages.success(request, _("DNS record has been updated."))
            else:
                errors = self.dnsaas.create_dns_record(
                    posted_form.cleaned_data, service=self.object.service
                )
                if not errors:
                    messages.success(request, _("DNS record has been created."))

            if errors:
                add_errors(posted_form, errors)
            else:
                return HttpResponseRedirect(".")

        kwargs["forms"] = forms
        return self.get(request, *args, **kwargs)
