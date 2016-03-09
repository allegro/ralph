# -*- coding: utf-8 -*-
from urllib.parse import urlencode

import requests
from django.conf import settings
from django.forms.models import BaseInlineFormSet

from ralph.dns.models import DNSRecord, RecordType


class DNSRecordInlineFormset(BaseInlineFormSet):
    _queryset = None

    def get_data_from_api(self):
        # ip_addresses = self.instance.ipaddress_set.all().values_list(
        #     'address', flat=True
        # )
        result = []
        url = '{}/{}/?{}'.format(
            settings.DNSAAS_URL,
            'api/records',
            urlencode({'type': 'A', 'limit': 100, 'offset': 0})  # TODO ?
        )
        headers = {'Authorization': 'Token {}'.format(settings.DNSAAS_TOKEN)}
        request = requests.get(url, headers=headers)
        json_data = request.json()
        # if json_data['next']:
        api_results = json_data.get('results', [])
        if api_results:
            for item in api_results:
                result.append(
                    DNSRecord(
                        name=item['name'],
                        type=RecordType.from_name(item['type'].lower()).id,
                        content=item['content'],
                        ptr=item['type'] == 'PTR'
                    )
                )

        return result

    def get_queryset(self):
        if self._queryset is None:
            self._queryset = self.get_data_from_api()
        return self._queryset

    def save(self, commit=True):
        # TODO save in API
        pass
