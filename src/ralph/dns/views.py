# -*- coding: utf-8 -*-
from urllib.parse import urlencode

import requests

from ralph.admin.views.extra import RalphDetailView
from django.forms import BaseFormSet, formset_factory
from django.conf import settings

from ralph.dns.forms import DNSRecordForm, RecordType


def get_api_result(url, headers=None):
    headers = {'Authorization': 'Token {}'.format(settings.DNSAAS_TOKEN)}
    if headers:
        headers.update(headers)
    request = requests.get(url, headers=headers)
    json_data = request.json()
    api_results = json_data.get('results', [])
    if json_data.get('next', None):
        _api_results = get_api_result(json_data['next'])
        api_results.extend(_api_results)
    return api_results


def get_dns_records(ipaddresses):
    """Gets DNS Records for `ipaddresses` by API call"""
    dns_records = []
    url = '{}/{}/?{}'.format(
        settings.DNSAAS_URL,
        'api/records',
        urlencode([
            ('type', 'A'),
            ('limit', 100),
            ('offset', 0)
        ])  # TODO ?
    )
    api_results = get_api_result(url)
    if api_results:
        for item in api_results:
            dns_records.append({
                'pk': 1,
                'name': item['name'],
                'type': RecordType.from_name(item['type'].lower()).id,
                'content': item['content'],
            })
    return dns_records


def update_dns_records(records):
    pass


def delete_dns_records(record_ids):
    headers = {'Authorization': 'Token {}'.format(settings.DNSAAS_TOKEN)}
    url = '{}/{}/?{}'.format(
        settings.DNSAAS_URL,
        'api/records',
    )
    request = requests.delete(url, headers=headers)


class DNSView(RalphDetailView):
    icon = 'chain-broken'
    name = 'dns_edit'
    label = 'DNS'
    url_name = 'dns_edit'
    template_name = 'dns/dns_edit.html'

    def get_formset(self):
        FormSet = formset_factory(  # noqa
            DNSRecordForm, formset=BaseFormSet, extra=1,
            can_delete=True
        )
        initial = get_dns_records(
            self.object.ipaddress_set.all().values_list(
                'address', flat=True
            )
        )
        return FormSet(
            initial=initial,
            # initial=initial if not self.request.POST else {},
            data=self.request.POST or None
        )

    def get(self, request, *args, **kwargs):
        kwargs['formset'] = self.get_formset()
        return super().get(request, *kwargs, **kwargs)

    def post(self, request, *args, **kwargs):
        formset = self.get_formset()
        if formset.is_valid():
            to_delete = []
            to_update = []
            for item in formset.cleaned_data:
                if item['DELETE']:
                    to_delete.append(item['pk'])
                else:
                    to_update.append(item)

            if to_delete:
                delete_dns_records(to_delete)
            if to_update:
                update_dns_records(to_update)

        kwargs['formset'] = formset
        return super().get(request, *args, **kwargs)
