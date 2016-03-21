# -*- coding: utf-8 -*-
import logging

from django.http import HttpResponseRedirect

from ralph.admin.views.extra import RalphDetailView
from ralph.dns.dnsaas import DNSaaS
from ralph.dns.forms import DNSRecordForm

logger = logging.getLogger(__name__)


class DNSView(RalphDetailView):
    icon = 'chain-broken'
    name = 'dns_edit'
    label = 'DNS'
    url_name = 'dns_edit'
    template_name = 'dns/dns_edit.html'

    def __init__(self, *args, **kwargs):
        self.dnsaas = DNSaaS()
        return super().__init__(*args, **kwargs)

    def get_forms(self):
        forms = []
        initial = self.dnsaas.get_dns_records(
            self.object.ipaddress_set.all().values_list(
                'address', flat=True
            )
        )
        for item in initial:
            forms.append(DNSRecordForm(item))

        forms.append(DNSRecordForm())
        return forms

    def get(self, request, *args, **kwargs):
        kwargs['forms'] = self.get_forms()
        return super().get(request, *kwargs, **kwargs)

    def post(self, request, *args, **kwargs):
        forms = self.get_forms()
        current_form = DNSRecordForm(request.POST)
        for i, form in enumerate(forms):
            if (
                str(form.data.get('pk', '')) ==
                str(current_form.data.get('pk', ''))
            ):
                forms[i] = current_form
                break

        if current_form.is_valid():
            if current_form.data.get('delete'):
                errors = self.dnsaas.delete_dns_records(form.data['pk'])
            elif current_form.cleaned_data.get('pk'):
                errors = self.dnsaas.update_dns_records(
                    current_form.cleaned_data
                )
            else:
                errors = self.dnsaas.create_dns_records(
                    current_form.cleaned_data
                )

            if errors:
                for k, v in errors.items():
                    for er in v:
                        current_form.add_error(k, er)
            else:
                return HttpResponseRedirect('.')

        kwargs['forms'] = forms
        return super().get(request, *args, **kwargs)
