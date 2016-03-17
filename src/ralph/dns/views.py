# -*- coding: utf-8 -*-
import logging

from django.forms import BaseFormSet, formset_factory
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

    def get_formset(self):
        FormSet = formset_factory(  # noqa
            DNSRecordForm, formset=BaseFormSet, extra=2,
            can_delete=True
        )
        initial = self.dnsaas.get_dns_records(
            self.object.ipaddress_set.all().values_list(
                'address', flat=True
            )
        )
        return FormSet(
            data=self.request.POST or None,
            initial=initial,
        )

    def get(self, request, *args, **kwargs):
        kwargs['formset'] = self.get_formset()
        return super().get(request, *kwargs, **kwargs)

    def post(self, request, *args, **kwargs):
        formset = self.get_formset()
        if formset.is_valid():
            for i, form in enumerate(formset.forms):
                if form.cleaned_data.get('DELETE'):
                    self.dnsaas.delete_dns_records(form.cleaned_data['pk'])
                elif form.has_changed():
                    if form.cleaned_data['pk']:
                        self.dnsaas.update_dns_records(form.cleaned_data)
                    else:
                        self.dnsaas.create_dns_records(form.cleaned_data)
            return HttpResponseRedirect('.')

        kwargs['formset'] = formset
        return super().get(request, *args, **kwargs)
