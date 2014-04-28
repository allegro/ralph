# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import random
import thread
import time

import MySQLdb
import requests
import sqlalchemy as sqla
import yaml

from django.conf import settings

from ralph.discovery.models import IPAddress, SERIAL_BLACKLIST
from ralph.scan.errors import Error
from ralph.scan.facts import (
    handle_facts,
    handle_facts_3ware_disks,
    handle_facts_hpacu,
    handle_facts_ip_addresses,
    handle_facts_megaraid,
    handle_facts_os,
    handle_facts_packages,
    handle_facts_smartctl,
    handle_facts_wwn,
)
from ralph.scan.lshw import Error as LshwError
from ralph.scan.lshw import handle_lshw
from ralph.scan.plugins import get_base_result_template
from ralph.util import network, uncompress_base64_data


SETTINGS = settings.SCAN_PLUGINS.get(__name__, {})
ENGINES = {}


class PuppetBaseProvider(object):

    def get_facts(self, ip_addresses, hostnames, messages=[]):
        raise NotImplementedError()


class PuppetAPIProvider(PuppetBaseProvider):

    def __init__(self, api_url):
        self.api_url = api_url

    def get_facts(self, ip_addresses, hostnames, messages=[]):
        return self._get_all_facts_by_hostnames(hostnames)

    def _get_all_facts_by_hostnames(self, hostnames):
        def construct_ruby_object(loader, suffix, node):
            return loader.construct_yaml_map(node)

        def construct_ruby_sym(loader, node):
            return loader.construct_yaml_str(node)

        yaml.add_multi_constructor(u"!ruby/object:", construct_ruby_object)
        yaml.add_constructor(u"!ruby/sym", construct_ruby_sym)
        for hostname in hostnames:
            data = self._get_data_for_hostname(hostname)
            if data:
                return yaml.load(data)['values']

    def _get_data_for_hostname(self, hostname):
        response = requests.get(
            "%(base_url)s/%(hostname)s" % dict(
                base_url=self.api_url,
                hostname=hostname,
            ),
            headers={'Accept': 'yaml'},
            verify=False,
        )
        if response.status_code == requests.codes.ok:
            return response.text


class PuppetDBProvider(PuppetBaseProvider):

    def __init__(self, db_url):
        self.db_url = db_url
        self.conn = self._connect_db()

    def _connect_db(self, force_reconnect=False):
        thread_id = thread.get_ident()
        if force_reconnect and thread_id in ENGINES:
            del ENGINES[thread_id]
        conn = None
        try:
            engine = ENGINES[thread_id]
            conn = engine.connect()
            _test = conn.execute("SELECT 1")
            _test.fetchall()
        except (KeyError, MySQLdb.OperationalError):
            if conn:
                conn.close()
            engine = sqla.create_engine(self.db_url, pool_recycle=3600)
            ENGINES[thread_id] = engine
            conn = engine.connect()
        return conn

    def get_facts(self, ip_addresses, hostnames, messages=[]):
        return self._get_facts(ip_addresses, hostnames, messages)

    def _get_facts(self, ip_addresses, hostnames, messages=[]):
        try:
            facts = self._get_facts_by_ip_addresses(ip_addresses)
            if not facts and hostnames:
                facts = self._get_facts_by_hostnames(hostnames)
        except MySQLdb.OperationalError as e:
            messages.append(unicode(e))
            if all((
                e.args[0] in (1205, 1213),
                'try restarting transaction' in e.args[1],
            )):
                time.sleep(random.choice(range(10)) + 1)
                self.conn = self._connect_db(True)
                return self._get_facts(ip_addresses, hostnames, messages)
            raise
        return facts

    def _get_facts_by_ip_addresses(self, ip_addresses):
        facts = None
        for ip_address in ip_addresses:
            rows = self.conn.execute(
                """
                    SELECT fn.name, fv.value
                    FROM hosts h, fact_values fv, fact_names fn
                    WHERE h.ip=%s AND fv.host_id=h.id
                    AND fv.fact_name_id=fn.id
                """,
                ip_address,
            )
            _facts = dict(rows.fetchall())
            if _facts:
                if _facts['virtual'] == 'zone':
                    continue
                if not facts:
                    facts = _facts
                else:
                    raise Error(
                        "More than 1 machine reported by Puppet for "
                        "this IP set: {}".format(', '.join(ip_addresses)),
                    )
        return facts

    def _get_facts_by_hostnames(self, hostnames):
        facts = None
        for hostname in hostnames:
            rows = self.conn.execute(
                """
                    SELECT fn.name, fv.value
                    FROM hosts h, fact_values fv, fact_names fn
                    WHERE h.name=%s AND fv.host_id=h.id
                    AND fv.fact_name_id=fn.id
                """,
                hostname,
            )
            _facts = dict(rows.fetchall())
            if _facts:
                if not facts:
                    facts = _facts
                else:
                    raise Error(
                        "More than 1 machine reported by Puppet for "
                        "this hostname set: {}".format(', '.join(hostnames)),
                    )
        return facts


def _get_ip_addresses_hostnames_sets(ip):
    hostnames_set = set()
    hostname = network.hostname(ip)
    if hostname:
        hostnames_set.add(hostname)
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


def _is_host_virtual(facts):
    is_virtual = facts.get('virtual', 'physical') not in (
        'physical', 'openvz', 'openvzhn',
    )
    if facts.get('manufacturer') == 'Bochs' and not is_virtual:
        facts['virtual'] = 'virtual'
        is_virtual = True
    return is_virtual


def _parse_lshw(lshw, is_virtual, sn=None):
    data = uncompress_base64_data(lshw)
    if sn in SERIAL_BLACKLIST:
        sn = None
    device_info = handle_lshw(data, is_virtual)
    if sn:
        device_info['serial_number'] = sn
    return device_info


def _parse_facts(facts, is_virtual=False):
    return handle_facts(facts, is_virtual)


def _merge_disks_results(disks, new_disks):
    result = []
    for disk in disks:
        disk_sn = disk.get('serial_number')
        if not disk_sn:
            result.append(disk)
            continue
        merged = False
        for i, new_disk in enumerate(new_disks):
            if new_disk['serial_number'] == disk_sn:
                disk.update(new_disk)
                result.append(disk)
                merged = True
                break
        if merged:
            new_disks.pop(i)
        else:
            result.append(disk)
    result.extend(new_disks)
    return result


def _puppet(provider, ip_address, messages=[]):
    ip_addresses_set, hostnames_set = _get_ip_addresses_hostnames_sets(
        ip_address,
    )
    facts = provider.get_facts(ip_addresses_set, hostnames_set, messages)
    if not facts:
        raise Error('Host config not found.')
    is_virtual = _is_host_virtual(facts)
    if 'lshw' in facts:
        device_info = _parse_lshw(facts['lshw'], is_virtual)
    else:
        device_info = _parse_facts(facts, is_virtual)
    ip_addresses = handle_facts_ip_addresses(facts)
    if ip_addresses:
        device_info['system_ip_addresses'] = ip_addresses
    else:
        device_info['system_ip_addresses'] = [ip_address]
    disk_shares = handle_facts_wwn(facts)
    if disk_shares:
        device_info['disk_shares'] = disk_shares
    disks = device_info.get('disks', [])
    disks = _merge_disks_results(
        disks,
        handle_facts_3ware_disks(facts),
    )
    disks = _merge_disks_results(
        disks,
        handle_facts_smartctl(facts),
    )
    disks = _merge_disks_results(
        disks,
        handle_facts_hpacu(facts),
    )
    disks = _merge_disks_results(
        disks,
        handle_facts_megaraid(facts),
    )
    device_info['disks'] = disks
    installed_software = handle_facts_packages(facts)
    if installed_software:
        device_info['installed_software'] = installed_software
    device_info.update(handle_facts_os(facts, is_virtual))
    return device_info


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
        device_info = _puppet(puppet_provider, ip_address, messages)
    except (LshwError, Error) as e:
        messages.append(unicode(e))
        result['status'] = 'error'
    else:
        result.update({
            'status': 'success',
            'device': device_info,
        })
    return result
