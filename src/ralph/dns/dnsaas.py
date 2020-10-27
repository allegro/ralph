# -*- coding: utf-8 -*-
import json
import logging
from urllib.parse import urlencode, urljoin, parse_qsl

import requests
from dj.choices import Choices
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from typing import Optional, List, Tuple

logger = logging.getLogger(__name__)

QueryParams = List[Tuple[str, str]]


class RecordType(Choices):
    _ = Choices.Choice

    a = _('A')
    txt = _('TXT')
    cname = _('CNAME')


class DNSaaS:

    def __init__(self, headers: dict = None):
        # TODO: ograć tu oautha
        self.session = requests.Session()
        _headers = {
            'Authorization': 'Token {}'.format(settings.DNSAAS_TOKEN),
            'Content-Type': 'application/json',
            'User-agent': 'Ralph/DNSaaS/Client'
        }
        if headers is not None:
            _headers.update(headers)
        self.session.headers.update(_headers)

    @staticmethod
    def build_url(resource_name: str, id: int = None, get_params: QueryParams = None) -> str:
        """
        Return Url for DNSAAS endpoint

        Args:
            resource_name: Resource name (example: domains)
            id: Record ID,
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

    @staticmethod
    def _set_page_qp(url: str, page: int):
        url_qp = url.split('?')
        url = url_qp[0]
        qp = []
        if len(url_qp) == 2:
            qp = parse_qsl(url_qp[1])
            for index, query_param in enumerate(qp):
                if query_param[0] == 'page':
                    qp.pop(index)
        qp.extend([('page', str(page)), ])

        result_url = "{}?{}".format(url, urlencode(qp))
        return result_url

    def get_api_result(self, url: str, page: int = 0) -> List[dict]:
        """
        Returns 'results' from DNSAAS API.

        Args:
            :str url: Url to API
            :int page:

        Returns:
            list of records

        """
        status_code, json_data = self._get(url)
        api_results = json_data.get('content', [])
        if not json_data.get('last', None):
            page = page + 1
            next_url = self._set_page_qp(url, page)
            _api_results = self.get_api_result(next_url, page=page)
            api_results.extend(_api_results)
        return api_results

    def get_dns_records(self, ipaddresses: List[str]) -> List[dict]:
        """Gets DNS Records for `ipaddresses` by API call"""
        dns_records = []
        if not ipaddresses:
            return []
        ipaddresses = [('ip', i) for i in ipaddresses]
        url = self.build_url(
            'records',
            get_params=[
                           ('size', '100'),
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

    def update_dns_record(self, record: dict) -> Optional[dict]:
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

    @staticmethod
    def _response2result(response: requests.Response) -> Optional[dict]:
        if response.status_code == 500:
            return {
                'non_field_errors': ['Internal Server Error from DNSAAS']
            }
        elif response.status_code != 201 and response.status_code != 204:
            return response.json()

    def create_dns_record(self, record: dict, service=None) -> Optional[dict]:
        """
        Create new DNS record.

        Args:
            record: Record cleaned data
            service:

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

    def _send_request_to_dnsaas(self, request_method: str, url: str, json_data: dict = None) -> requests.Response:
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

    def _post(self, url: str, data: dict) -> [int, Optional[dict]]:
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

    def _delete(self, url: str) -> [int, Optional[dict]]:
        response = self._send_request_to_dnsaas('DELETE', url)

        return response.status_code, self._response2result(response)

    def _get(self, url: str) -> [int, Optional[dict]]:
        response = self._send_request_to_dnsaas('GET', url)

        return response.status_code, self._response2result(response)

    def _patch(self, url: str, data: dict) -> [int, Optional[dict]]:
        response = self._send_request_to_dnsaas('PATCH', url, json_data=data)
        return response.status_code, self._response2result(response)

    def delete_dns_record(self, record_id: int) -> dict:
        """
        Delete record in DNSAAS.

        Args:
            record_id: ID to delete

        Returns:
            Validation error from API or None if delete correct
        """
        url = self.build_url('records', id=record_id)
        _, data = self._delete(url)

        return data

    def send_ipaddress_data(self, ip_record_data: dict):
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
