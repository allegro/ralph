# -*- coding: utf-8 -*-
import logging
from urllib.parse import urlencode, urljoin

import requests
from django.conf import settings
from django.contrib import messages
from django.forms import BaseFormSet, formset_factory
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _

from ralph.admin.views.extra import RalphDetailView
from ralph.dns.forms import DNSRecordForm, RecordType

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
                settings.DNS_AUTO_PTR_ALWAYS if item['ptr'] and
                item['type'] == RecordType.a.id
                else settings.DNS_AUTO_PTR_NEVER
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
        initial = get_dns_records(
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

            if to_delete and delete_dns_records(to_delete):
                messages.error(
                    request, _('An error occurred while deleting a record')
                )
            if to_update and update_dns_records(to_update):
                messages.error(
                    request, _('An error occurred while updating a record')
                )

            return HttpResponseRedirect('.')

        kwargs['formset'] = formset
        return super().get(request, *args, **kwargs)
