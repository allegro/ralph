# -*- coding: utf-8 -*-
import logging

from django.contrib import messages
from django.forms import BaseFormSet, formset_factory
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _

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

    def get_formset(self):
        FormSet = formset_factory(  # noqa
            DNSRecordForm, formset=BaseFormSet, extra=2,
            can_delete=True
        )
        dnsaas = DNSaaS()
        initial = dnsaas.get_dns_records(
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
            to_delete = []
            to_update = []
            for form in formset.forms:
                if form.cleaned_data.get('DELETE'):
                    to_delete.append(form.cleaned_data['pk'])
                elif form.has_changed():
                    to_update.append(form.cleaned_data)

            dnsaas = DNSaaS()
            if to_delete and dnsaas.delete_dns_records(to_delete):
                messages.error(
                    request, _('An error occurred while deleting a record')
                )
            if to_update and dnsaas.update_dns_records(to_update):
                messages.error(
                    request, _('An error occurred while updating a record')
                )

            return HttpResponseRedirect('.')

        kwargs['formset'] = formset
        return super().get(request, *args, **kwargs)
