# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging

from django.db.models import Q

from ralph.discovery.models import (
    Connection,
    ConnectionType,
    NetworkConnection,
)
from ralph.scan.automerger import select_data
from ralph.scan.data import (
    append_merged_proposition,
    connection_from_data,
    find_devices,
    get_device_data,
    get_external_results_priorities,
    merge_data,
)


logger = logging.getLogger("LLDP_CONNECTIONS")


def _network_connections_in_results(data):
    for plugin_name, plugin_result in data.iteritems():
        if plugin_result['status'] == 'error':
            continue
        if 'device' not in plugin_result:
            continue
        if 'connections' in plugin_result['device']:
            for conn in plugin_result['device']['connections']:
                if conn['connection_type'] == ConnectionType.network.name:
                    return True
    return False


def _create_or_update_connection(device, connection_data):
    connection = None
    if connection_data['connection_type'] != 'network':
        return
    try:
        connection = connection_from_data(device, connection_data)
    except ValueError as e:
        sn = ''
        if 'connected_device_serial_number' in connection_data:
            sn = connection_data['connected_device_serial_number']
        mac_addresses = ''
        if 'connected_device_mac_addresses' in connection_data:
            mac_addresses = connection_data['connected_device_mac_addresses']
        ip_addresses = ''
        if 'connected_device_ip_addresses' in connection_data:
            mac_addresses = connection_data['connected_device_ip_addresses']
        msg = """
            Connection creating failed.
            Connection params: sn={}; mac_addresses={}; ip_addresses={};
            Exception message: {}.
        """.format(sn, mac_addresses, ip_addresses, unicode(e))
        logger.exception(msg)
    else:
        connection_details = connection_data.get('details', {})
        if connection_details:
            outbound_port = connection_details.get('outbound_port')
            inbound_port = connection_details.get('inbound_port')
            try:
                details = NetworkConnection.objects.get(connection=connection)
            except NetworkConnection.DoesNotExist:
                details = NetworkConnection(connection=connection)
            if outbound_port:
                details.outbound_port = outbound_port
            if inbound_port:
                details.inbound_port = inbound_port
            details.save()
    return connection


def _append_connections_to_device(device, data, external_priorities):
    device_data = get_device_data(device)
    full_data = merge_data(
        data,
        {
            'database': {'device': device_data},
        },
        only_multiple=True,
    )
    append_merged_proposition(full_data, device, external_priorities)
    selected_data = select_data(full_data, external_priorities)
    parsed_connections = set()
    for conn_data in selected_data.get('connections', []):
        conn = _create_or_update_connection(device, conn_data)
        if conn:
            parsed_connections.add(conn.pk)
    Connection.objects.filter(
        Q(outbound=device),
        Q(connection_type=ConnectionType.network),
        ~Q(pk__in=parsed_connections),
    ).delete()


def _lldp_connections(ip, data):
    if not _network_connections_in_results(data):
        return  # No reason to run it...
    external_priorities = get_external_results_priorities(data)
    devices = find_devices(data)
    if len(devices) == 0:
        logger.warning(
            'No device found for the IP address %s. '
            'There are some connections.' % ip.address
        )
        return
    elif len(devices) > 1:
        logger.warning(
            'Many devices found for the IP address %s. '
            'There are some connections.' % ip.address
        )
        return
    _append_connections_to_device(devices[0], data, external_priorities)


def run_job(ip, **kwargs):
    data = kwargs.get('plugins_results', {})
    _lldp_connections(ip, data)
