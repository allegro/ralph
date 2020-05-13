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
            'Authorization': 'Token {}'.format(settings.DNSAAS_TOKEN),
            'Content-Type': 'application/json'
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
        status_code, json_data = self._get(url)
        api_results = json_data.get('results', [])
        if json_data.get('next', None):
            _api_results = self.get_api_result(json_data['next'])
            api_results.extend(_api_results)
        return api_results

    def get_dns_records(self, ipaddresses):
        """Gets DNS Records for `ipaddresses` by API call"""
        dns_records = []
        if not ipaddresses:
            return []
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

        status_code, response_data = self._patch(url, data)
        if status_code != 200:
            return response_data

    @cache(skip_first=True)
    def get_domain(self, domain_name):
        """
        Return domain ID base on record name.

        Args:
            domain_name: Domain name

        Return:
            Domain ID from API or None if not exists
        """
        parts = domain_name.split('.')
        while parts:
            domain_name = '.'.join(parts)
            url = self.build_url('domains', get_params=[('name', domain_name)])
            result = self.get_api_result(url)
            if result:
                return result[0]['id']

            parts = parts[1:]
        return None

    def _response2result(self, response):
        if response.status_code == 500:
            return {
                'non_field_errors': ['Internal Server Error from DNSAAS']
            }
        elif response.status_code == 202:
            logger.error(
                "User '{}' has insufficient permission".format(
                    settings.DNSAAS_OWNER
                )
            )
            return {
                'non_field_errors': [
                    "Your request couldn't be handled, try later."
                ]
            }
        elif response.status_code != 201 and response.status_code != 204:
            return response.json()

    def create_dns_record(self, record, service=None):
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
        if service:
            data['service_uid'] = service.uid
        return self._post(url, data)[1]

    def _post(self, url, data):
        """
        Send post data to URL.

        Args:
            url: str endpoint url
            data: dict to send

        Returns:
            tuple (response status code, dict data)
        """
        logger.info("Sending POST request to DNSaaS to {}".format(url))
        response = self.session.post(url, json=data)
        return response.status_code, self._response2result(response)

    def _delete(self, url):
        logger.info("Sending DELETE request to DNSaaS to {}".format(url))
        response = self.session.delete(url)

        return response.status_code, self._response2result(response)

    def _get(self, url):
        logger.info("Sending GET request to DNSaaS to {}".format(url))
        response = self.session.get(url)

        return response.status_code, self._response2result(response)

    def _patch(self, url, data):
        logger.info("Sending PATCH request to DNSaaS to {}".format(url))

        response = self.session.patch(url, json=data)
        return response.status_code, self._response2result(response)

    def delete_dns_record(self, record_id):
        """
        Delete record in DNSAAS.

        Args:
            record_ids: ID's to delete

        Returns:
            Validation error from API or None if delete correct
        """
        url = self.build_url('records', id=record_id)
        _, data = self._delete(url)

        return data

    def send_ipaddress_data(self, ip_record_data):
        """
        Send data about IP address and hostname.

        Args:
            ip_record_data: dict contains keys: new, old, service_uid, action
                Structure of parameter:
                ``
                {
                    'old': {
                        'address': 127.0.0.1,
                        'hostname': 'localhost.local'
                    }
                    'new': {
                        'address': 127.0.0.1,
                        'hostname': 'localhost'
                    },
                    'service_uid': 'xxx-123',
                    'action': 'update'
                }
                ``
                ``old`` and ``new`` contains previous and next state of
                IP address record (in Ralph).
        Returns:
            JSON response from API
        """
        logger.info('Send update data: {}'.format(ip_record_data))
        url = self.build_url('ip_record')
        status_code, response_data = self._post(url, ip_record_data)
        if status_code >= 400:
            logger.error(
                'DNSaaS returned {} data: {}, send_data: {}'.format(
                    status_code, str(response_data), ip_record_data
                )
            )


dnsaas_client = DNSaaS()
