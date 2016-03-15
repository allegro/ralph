# -*- coding: utf-8 -*-
from urllib.parse import urlencode

import requests
from django.conf import settings
from django.forms.models import BaseInlineFormSet

from ralph.dns.models import DNSRecord, RecordType


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
    "Gets DNS Records for `ipaddresses` by API call"
    dns_records = []
    url = '{}/{}/?{}'.format(
        settings.DNSAAS_URL,
        'api/records',
        urlencode({'type': 'A', 'limit': 100, 'offset': 0})  # TODO ?
    )
    api_results = get_api_result(url)
    if api_results:
        for item in api_results:
            dns_records.append(
                DNSRecord(
                    name=item['name'],
                    type=RecordType.from_name(item['type'].lower()).id,
                    content=item['content'],
                )
            )
    return dns_records


class DNSRecordInlineFormset(BaseInlineFormSet):
    _queryset = None

    def get_data_from_api(self):
        #TODO: use real data
        ipaddresses = []
        # ip_addresses = self.instance.ipaddress_set.all().values_list(
        #     'address', flat=True
        # )
        dns_records = get_dns_records(ipaddresses)
        return dns_records

    def get_queryset(self):
        if self._queryset is None:
            self._queryset = self.get_data_from_api()
        return self._queryset

    def save(self, commit=True):
        # TODO save in API
        pass
