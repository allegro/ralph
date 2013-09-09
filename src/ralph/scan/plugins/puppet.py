# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.conf import settings

from ralph.discovery.models import IPAddress
from ralph.scan.plugins import get_base_result_template
from ralph.util import network


SETTINGS = settings.SCAN_PLUGINS.get(__name__, {})


class Error(Exception):
    pass


class PuppetBaseProvider(object):
    def get_facts(self, ip_addresses, hostnames):
        raise NotImplementedError()


class PuppetAPIProvider(PuppetBaseProvider):
    def __init__(self, api_url):
        self.api_url = api_url

    def get_facts(self, ip_addresses, hostnames):
        raise NotImplementedError()


class PuppetDBProvider(PuppetBaseProvider):
    def __init__(self, db_url):
        self.db_url = db_url

    def get_facts(self, ip_addresses, hostnames):
        raise NotImplementedError()


def _get_ip_addresses_hostnames_sets(ip):
    hostnames_set = {network.hostname(ip)}
    try:
        ip_address = IPAddress.objects.get(address=ip)
    except IPAddress.DoesNotExist:
        ip_addresses_set = {ip}
    else:
        if ip_address.device:
            ip_addresses_set = set()
            for ip in ip_address.device.ipaddress_set.all():
                ip_addresses_set.add(ip.address)
                if ip.hostname:
                    hostnames_set.add(ip.hostname)
        else:
            ip_addresses_set = {ip}
    return ip_addresses_set, hostnames_set


def _puppet(provider, ip_address):
    ip_addresses_set, hostnames_set = _get_ip_addresses_hostnames_sets(
        ip_address,
    )
    facts = provider.get_facts(ip_addresses_set, hostnames_set)
    if not facts:
        raise Error('Host config not found.')
    import pprint
    pprint.pprint(facts)
    return {}


def scan_address(ip_address, **kwargs):
    messages = []
    result = get_base_result_template('puppet', messages)
    puppet_api_url = SETTINGS.get('puppet_api_url')
    puppet_db_url = SETTINGS.get('puppet_db_url')
    if not puppet_api_url and not puppet_db_url:
        messages.append('Not configured.')
        result['status'] = 'error'
        return result
    if puppet_db_url:
        puppet_provider = PuppetDBProvider(puppet_db_url)
    else:
        puppet_provider = PuppetAPIProvider(puppet_api_url)
    try:
        device_info = _puppet(puppet_provider)
    except Error as e:
        messages.append(unicode(e))
        result['status'] = 'error'
    else:
        result.update({
            'status': 'success',
            'device': device_info,
        })
    return result

