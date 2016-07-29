# -*- coding: utf-8 -*-
import logging
from urllib.parse import urlencode, urljoin

import requests
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from ralph.dns.forms import RecordType
from ralph.helpers import cache

logger = logging.getLogger(__name__)


class DNSaaS:

    def __init__(self, headers=None):
        self.session = requests.Session()
        _headers = {
            'Authorization': 'Token {}'.format(settings.DNSAAS_TOKEN)
        }
        if headers is not None:
            _headers.update(headers)
        self.session.headers.update(_headers)

    def build_url(self, resource_name, id=None, version='v2', get_params=None):
        """
        Return Url for DNSAAS endpoint

        Args:
            resource_name: Resource name (example: domains)
            id: Record ID,
            version: Api Version
            get_params: List of tuple to URL GET params: (example:
                [('name', 'value')]
            )
        Returns:
            string url
        """
        result_url = urljoin(
            settings.DNSAAS_URL,
            'api/{}/{}/'.format(version, resource_name)
        )
        if id:
            result_url = "{}{}/".format(result_url, str(id))
        if get_params:
            result_url = "{}?{}".format(result_url, urlencode(get_params))

        return result_url

    def get_api_result(self, url):
        """
        Returns 'results' from DNSAAS API.

        Args:
            url: Url to API

        Returns:
            list of records
        """
        request = self.session.get(url)
        json_data = request.json()
        api_results = json_data.get('results', [])
        if json_data.get('next', None):
            _api_results = self.get_api_result(json_data['next'])
            api_results.extend(_api_results)
        return api_results

    def get_dns_records(self, ipaddresses):
        """Gets DNS Records for `ipaddresses` by API call"""
        dns_records = []
        ipaddresses = [('ip', i) for i in ipaddresses]
        url = self.build_url(
            'records',
            get_params=[
                ('limit', 100),
                ('offset', 0)
            ] + ipaddresses
        )
        api_results = self.get_api_result(url)
        ptrs = set([i['content'] for i in api_results if i['type'] == 'PTR'])

        for item in api_results:
            if item['type'] in {'A', 'CNAME', 'TXT'}:
                dns_records.append({
                    'pk': item['id'],
                    'name': item['name'],
                    'type': RecordType.from_name(item['type'].lower()).id,
                    'content': item['content'],
                    'ptr': item['name'] in ptrs and item['type'] == 'A',
                    'owner': settings.DNSAAS_OWNER
                })
        return sorted(dns_records, key=lambda x: x['type'])

    def update_dns_record(self, record):
        """
        Update DNS Record in DNSAAS

        Args:
            record: record cleaned data

        Returns:
            Validation error from API or None if update correct
        """
        url = self.build_url('records', id=record['pk'])
        data = {
            'name': record['name'],
            'type': RecordType.raw_from_id(int(record['type'])),
            'content': record['content'],
            'auto_ptr': (
                settings.DNSAAS_AUTO_PTR_ALWAYS if record['ptr'] and
                record['type'] == str(RecordType.a.id)
                else settings.DNSAAS_AUTO_PTR_NEVER
            ),
            'owner': settings.DNSAAS_OWNER
        }
        request = self.session.patch(url, data=data)
        if request.status_code == 500:
            return {
                'non_field_errors': [_('Internal Server Error from DNSAAS')]
            }
        elif request.status_code != 200:
            return request.json()

    @cache(skip_first=True)
    def get_domain(self, domain_name):
        """
        Return domain URL base on record name.

        Args:
            domain_name: Domain name

        Return:
            Domain URL from API or False if not exists
        """
        url = self.build_url('domains', get_params=[('name', domain_name)])
        result = self.get_api_result(url)
        if result:
            return result[0]['id']

    def _request2result(self, request):
        if request.status_code == 500:
            return {
                'non_field_errors': [_('Internal Server Error from DNSAAS')]
            }
        elif request.status_code == 202:
            logger.error(
                "User '{}' has insufficient permission".format(
                    settings.DNSAAS_OWNER
                )
            )
            return {
                'non_field_errors': [
                    _("Your request couldn't be handled, try later.")
                ]
            }
        elif request.status_code != 201:
            return request.json()

    def create_dns_record(self, record):
        """
        Create new DNS record.

        Args:
            records: Record cleaned data

        Returns:
            Validation error from API or None if create correct
        """

        url = self.build_url('records')
        domain_name = record['name'].split('.', 1)
        domain = self.get_domain(domain_name[-1])
        if not domain:
            logger.error(
                'Domain not found for record {}'.format(record)
            )
            return {'name': [_('Domain not found.')]}

        data = {
            'name': record['name'],
            'type': RecordType.raw_from_id(int(record['type'])),
            'content': record['content'],
            'auto_ptr': (
                settings.DNSAAS_AUTO_PTR_ALWAYS if record['ptr'] and
                record['type'] == RecordType.a.id
                else settings.DNSAAS_AUTO_PTR_NEVER
            ),
            'domain': domain,
            'owner': settings.DNSAAS_OWNER
        }
        request = self.session.post(url, data=data)
        return self._request2result(request)

    def delete_dns_record(self, record_id):
        """
        Delete record in DNSAAS

        Args:
            record_ids: ID's to delete

        Returns:
            Validation error from API or None if delete correct
        """
        url = self.build_url('records', id=record_id)
        request = self.session.delete(url)
        if request.status_code == 500:
            return {
                'non_field_errors': [_('Internal Server Error from DNSAAS')]
            }
        elif request.status_code != 204:
            return request.json()
