# -*- coding: utf-8 -*-
import json
import logging
from urllib.parse import urlencode, urljoin

import requests
from dj.choices import Choices
from django.conf import settings
from django.utils.translation import ugettext_lazy as _


logger = logging.getLogger(__name__)

class RecordType(Choices):
    _ = Choices.Choice

    a = _('A')
    txt = _('TXT')
    cname = _('CNAME')


class DNSaaS:

    def __init__(self, headers=None):
        # TODO(pbromber): Oauth comes here
        self.session = requests.Session()
        _headers = {
            'Authorization': 'Token {}'.format(settings.DNSAAS_TOKEN),
            'Content-Type': 'application/json',
            'User-agent': 'Ralph/DNSaaS/Client'
        }
        if headers is not None:
            _headers.update(headers)
        self.session.headers.update(_headers)

    def build_url(self, resource_name, id=None, get_params=None):
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
            'api/{}/'.format(resource_name)
        )
        if id:
            result_url = "{}{}/".format(result_url, str(id))
        if get_params:
            result_url = "{}?{}".format(result_url, urlencode(get_params))
        return result_url

    def _add_query_params(self, url, query_params):
        result_url = "{}?{}".format(url, urlencode(query_params))
        return result_url

    def get_api_result(self, url, query_params=None, page=0):
        """
        Returns 'results' from DNSAAS API.

        Args:
            url: Url to API

        Returns:
            list of records
        """
        if query_params:
            get_url = "{}?{}".format(url, urlencode(query_params))
        status_code, json_data = self._get(get_url)
        api_results = json_data.get('content', [])
        if not json_data.get('last', None):
            page = page + 1
            next_url = self._add_query_params(url, ('page', page))
            _api_results = self.get_api_result(next_url, page=page)
            api_results.extend(_api_results)
        return api_results

    def get_dns_records(self, ipaddresses):
        """Gets DNS Records for `ipaddresses` by API call"""
        dns_records = []
        if not ipaddresses:
            return []
        ipaddresses = [('ip', i) for i in ipaddresses]
        url = self.build_url(
            'records'
        )
        url = self._add_query_params(url, [('size', 100), ] + ipaddresses)
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
        }

        status_code, response_data = self._patch(url, data)
        if status_code != 202:
            return response_data

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

        data = {
            'name': record['name'],
            'type': RecordType.raw_from_id(int(record['type'])),
            'content': record['content'],
        }
        if service:
            data['service_uid'] = service.uid
        else:
            logger.error(
                'Service not found'
            )
            return {'name': [_('Service not found.')]}
        return self._post(url, data)[1]

    def _send_request_to_dnsaas(self, request_method, url, json_data=None):
        try:
            response = self.session.request(
                method=request_method,
                url=url,
                json=json_data,
                timeout=float(settings.DNSAAS_TIMEOUT)
            )
            logger.info(
                "Sent {} request to DNSaaS to {}".format(
                    request_method, url
                ),
                extra={
                    'request_data': json.dumps(json_data),
                    'response_status': response.status_code,
                    'response_content': response.text
                }
            )

            return response
        except Exception:
            logger.exception(
                "Sending {} request to DNSaaS to {} failed.".format(
                    request_method, url
                ),
                extra={
                    'request_data': json.dumps(json_data)
                }
            )
            raise

    def _post(self, url, data):
        """
        Send post data to URL.

        Args:
            url: str endpoint url
            data: dict to send

        Returns:
            tuple (response status code, dict data)
        """
        response = self._send_request_to_dnsaas('POST', url, json_data=data)
        return response.status_code, self._response2result(response)

    def _delete(self, url):
        response = self._send_request_to_dnsaas('DELETE', url)

        return response.status_code, self._response2result(response)

    def _get(self, url):
        response = self._send_request_to_dnsaas('GET', url)

        return response.status_code, self._response2result(response)

    def _patch(self, url, data):
        response = self._send_request_to_dnsaas('PATCH', url, json_data=data)
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
