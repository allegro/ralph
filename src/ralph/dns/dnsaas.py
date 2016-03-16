# -*- coding: utf-8 -*-
import logging
from urllib.parse import urlencode, urljoin

import requests
from django.conf import settings

from ralph.dns.forms import RecordType

logger = logging.getLogger(__name__)


def get_api_kwargs(url, data=None, headers=None):
    if headers is None:
        headers = {}
    headers.update({'Authorization': 'Token {}'.format(settings.DNSAAS_TOKEN)})

    return {'url': url, 'data': data, 'headers': headers}


def get_api_result(url):
    request = requests.get(**get_api_kwargs(url))
    json_data = request.json()
    api_results = json_data.get('results', [])
    if json_data.get('next', None):
        _api_results = get_api_result(json_data['next'])
        api_results.extend(_api_results)
    return api_results


def get_dns_records(ipaddresses):
    """Gets DNS Records for `ipaddresses` by API call"""
    dns_records = []
    ipaddresses = [('ip', i) for i in ipaddresses]
    url = '{}/{}/?{}'.format(
        settings.DNSAAS_URL,
        'api/records',
        urlencode([
            ('limit', 100),
            ('offset', 0)
        ] + ipaddresses)
    )
    api_results = get_api_result(url)
    ptr_list = set([i['content'] for i in api_results if i['type'] == 'PTR'])

    for item in api_results:
        if item['type'] in {'A', 'CNAME', 'TXT'}:
            dns_records.append({
                'pk': item['id'],
                'name': item['name'],
                'type': RecordType.from_name(item['type'].lower()).id,
                'content': item['content'],
                'ptr': item['name'] in ptr_list
            })
    return dns_records


def update_dns_records(records):
    error = False
    for item in records:
        url = urljoin(
            settings.DNSAAS_URL, 'api/records/{}/'.format(item['pk'])
        )
        data = {
            'name': item['name'],
            'type': RecordType.raw_from_id(int(item['type'])),
            'content': item['content'],
            'auto_ptr': (
                settings.DNSAAS_AUTO_PTR_ALWAYS if item['ptr'] and
                item['type'] == RecordType.a.id
                else settings.DNSAAS_AUTO_PTR_NEVER
            )
        }
        request = requests.patch(**get_api_kwargs(url, data=data))
        if request.status_code != 200:
            logger.error(
                'Error from DNS API {}: {}'.format(url, request.json())
            )
            error = True

    return error


def delete_dns_records(record_ids):
    error = False
    for record_id in record_ids:
        url = urljoin(
            settings.DNSAAS_URL, 'api/records/{}/'.format(record_id)
        )
        request = requests.delete(**get_api_kwargs(url))
        if request.status_code != 204:
            error = True
            logger.error(
                'Error from DNS API {}: {}'.format(url, request.json())
            )

    return error
