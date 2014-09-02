# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.conf import settings

from ralph.discovery.models import ConnectionType
from ralph.scan.errors import Error
from ralph.scan.plugins import get_base_result_template
from ralph.discovery.snmp import snmp_walk


SETTINGS = settings.SCAN_PLUGINS.get(__name__, {})


def _get_device_interfaces_map(ip_address, snmp_community, snmp_version):
    items = snmp_walk(
        ip_address,
        snmp_community,
        [int(chunk) for chunk in "1.0.8802.1.1.2.1.3.7.1.3".split(".")],
        snmp_version
    )
    interfaces_map = {}
    for item in items:
        interfaces_map[unicode(item[0][0]).split(".")[-1]] = unicode(
            item[0][1]
        )
    return interfaces_map


def _get_remote_mac_addresses_map(ip_address, snmp_community, snmp_version):
    items = snmp_walk(
        ip_address,
        snmp_community,
        [int(chunk) for chunk in "1.0.8802.1.1.2.1.4.1.1.5".split(".")],
        snmp_version
    )
    mac_addresses_map = {}
    for item in items:
        mac_addresses_map[unicode(item[0][0]).split(".")[-2]] = "".join(
            "{:0>2}".format(str(hex(ord(chunk)))[2:]) for chunk in item[0][1]
        ).upper()
    return mac_addresses_map


def _get_remote_ip_addresses_map(ip_address, snmp_community, snmp_version):
    items = snmp_walk(
        ip_address,
        snmp_community,
        [int(chunk) for chunk in "1.0.8802.1.1.2.1.4.2.1.3".split(".")],
        snmp_version
    )
    ip_addresses_map = {}
    for item in items:
        ip_addresses_map[
            unicode(item[0][0]).split('.')[-8]
        ] = ".".join(unicode(item[0][0]).split('.')[-4:])
    return ip_addresses_map


def _get_remote_connected_ports_map(ip_address, snmp_community, snmp_version):
    items = snmp_walk(
        ip_address,
        snmp_community,
        [int(chunk) for chunk in "1.0.8802.1.1.2.1.4.1.1.8".split(".")],
        snmp_version
    )
    ports_map = {}
    for item in items:
        ports_map[unicode(item[0][0]).split(".")[-2]] = unicode(item[0][1])
    return ports_map


def _snmp_lldp(
    ip_address, snmp_community, snmp_version, messages=[]
):
    try:
        interfaces_map = _get_device_interfaces_map(
            ip_address, snmp_community, snmp_version
        )
        mac_addresses_map = _get_remote_mac_addresses_map(
            ip_address, snmp_community, snmp_version
        )
        ip_addresses_map = _get_remote_ip_addresses_map(
            ip_address, snmp_community, snmp_version
        )
        ports_map = _get_remote_connected_ports_map(
            ip_address, snmp_community, snmp_version
        )
    except TypeError:
        raise Error("No answer.")
    except IndexError:
        raise Error("Incorrect answer.")
    connections = []
    for item_id, mac_address in mac_addresses_map.iteritems():
        connection = {
            'connection_type': ConnectionType.network.name,
            'connected_device_mac_addresses': mac_address
        }
        connected_ip = ip_addresses_map.get(item_id)
        if connected_ip:
            connection['connected_device_ip_addresses'] = connected_ip
        details = {}
        outbound_port = interfaces_map.get(item_id)
        if outbound_port:
            details['outbound_port'] = outbound_port
        inbound_port = ports_map.get(item_id)
        if inbound_port:
            details['inbound_port'] = inbound_port
        if details:
            connection['details'] = details
        connections.append(connection)
    return {
        'system_ip_addresses': [ip_address],
        'connections': connections
    }


def scan_address(ip_address, **kwargs):
    snmp_version = kwargs.get('snmp_version', '2c') or '2c'
    if snmp_version == '3':
        snmp_community = SETTINGS['snmp_v3_auth']
    else:
        snmp_community = str(kwargs['snmp_community'])
    messages = []
    result = get_base_result_template('snmp_macs', messages)
    try:
        info = _snmp_lldp(
            ip_address,
            snmp_community,
            snmp_version,
            messages,
        )
    except Error as e:
        messages.append(unicode(e))
        result['status'] = "error"
    else:
        result.update({
            'status': 'success',
            'device': info,
        })
    return result
