# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import mock

from django.test import TestCase

from ralph.discovery.models import (
    Connection,
    ConnectionType,
    Device,
    DeviceModel,
    DeviceType,
)
from ralph.scan.postprocess.lldp_connections import (
    _append_connections_to_device,
    _create_or_update_connection,
    _network_connections_in_results,
)


class LldpConnectionsPostprocessTest(TestCase):

    def test__network_connections_in_results(self):
        self.assertTrue(
            _network_connections_in_results(
                {
                    ("plugin1",): {
                        "status": "success",
                        "device": {
                            "connections": [
                                {
                                    "connection_type": "network"
                                }
                            ]
                        }
                    }
                }
            )
        )
        self.assertTrue(
            _network_connections_in_results(
                {
                    ("plugin1",): {
                        "status": "success",
                        "device": {
                            "connections": []
                        }
                    },
                    ("plugin2",): {
                        "status": "success",
                        "device": {
                            "connections": [
                                {
                                    "connection_type": "network"
                                }
                            ]
                        }
                    }
                }
            )
        )
        self.assertTrue(
            _network_connections_in_results(
                {
                    ("plugin1",): {
                        "status": "success",
                        "device": {
                            "connections": []
                        }
                    },
                    ("plugin2",): {
                        "status": "success",
                        "device": {}
                    },
                    ("plugin3",): {
                        "status": "success",
                        "device": {
                            "connections": [
                                {
                                    "connection_type": "network"
                                }
                            ]
                        }
                    }
                }
            )
        )
        self.assertFalse(
            _network_connections_in_results(
                {
                    ("plugin1",): {
                        "status": "error",
                    }
                }
            )
        )
        self.assertFalse(
            _network_connections_in_results(
                {
                    ("plugin1",): {
                        "status": "success",
                    }
                }
            )
        )
        self.assertFalse(
            _network_connections_in_results(
                {
                    ("plugin1",): {
                        "status": "success",
                        "device": {}
                    }
                }
            )
        )
        self.assertFalse(
            _network_connections_in_results(
                {
                    ("plugin1",): {
                        "status": "success",
                        "device": {
                            "connections": []
                        }
                    }
                }
            )
        )
        self.assertFalse(
            _network_connections_in_results(
                {
                    ("plugin1",): {
                        "status": "success",
                        "device": {
                            "connections": [
                                {
                                    "connection_type": "foo"
                                }
                            ]
                        }
                    }
                }
            )
        )

    def test_create_or_update_connection(self):
        model = DeviceModel.objects.create(
            type=DeviceType.rack_server,
            name="DevModel F1"
        )
        master_device = Device.objects.create(
            model=model,
            sn='sn_1',
            name='dev1.dc1'
        )
        connected_device = Device.objects.create(
            model=model,
            sn='sn_2',
            name='dev2.dc1'
        )
        connection = Connection.objects.create(
            connection_type=ConnectionType.network,
            outbound=master_device,
            inbound=connected_device
        )
        with mock.patch(
            'ralph.scan.postprocess.lldp_connections.connection_from_data'
        ) as connection_from_data_mock:
            connection_from_data_mock.return_value = connection
            conn = _create_or_update_connection(
                master_device,
                {
                    'connection_type': 'network',
                    'details': {
                        'outbound_port': 'eth0',
                        'inbound_port': 'eth1'
                    },
                    'connected_device_serial_number': 'sn_2'
                }
            )
            self.assertIsNotNone(conn)
            self.assertEqual(conn.networkconnection.outbound_port, "eth0")
            self.assertEqual(conn.networkconnection.inbound_port, "eth1")
        connection.networkconnection.outbound_port, "ziew1"
        connection.networkconnection.outbound_port, "ziew2"
        connection.networkconnection.save()
        with mock.patch(
            'ralph.scan.postprocess.lldp_connections.connection_from_data'
        ) as connection_from_data_mock:
            connection_from_data_mock.return_value = Connection.objects.get(
                pk=connection.pk
            )
            conn = _create_or_update_connection(
                master_device,
                {
                    'connection_type': 'network',
                    'details': {
                        'outbound_port': 'gr0',
                        'inbound_port': 'gr2'
                    },
                    'connected_device_serial_number': 'sn_2'
                }
            )
            self.assertIsNotNone(conn)
            self.assertEqual(conn.networkconnection.outbound_port, "gr0")
            self.assertEqual(conn.networkconnection.inbound_port, "gr2")
        with mock.patch(
            'ralph.scan.postprocess.lldp_connections.connection_from_data'
        ) as connection_from_data_mock:
            connection_from_data_mock.return_value = Connection.objects.get(
                pk=connection.pk
            )
            conn = _create_or_update_connection(
                master_device,
                {
                    'connection_type': 'foo',
                    'details': {
                        'outbound_port': 'eth0',
                        'inbound_port': 'eth1'
                    },
                    'connected_device_serial_number': 'sn_2'
                }
            )
            self.assertIsNone(conn)

    def test_append_connections_to_device(self):
        model = DeviceModel.objects.create(
            type=DeviceType.rack_server,
            name="DevModel F1"
        )
        master_device = Device.objects.create(
            model=model,
            sn='sn_1',
            name='dev1.dc1'
        )
        connected_device_1 = Device.objects.create(
            model=model,
            sn='sn_2',
            name='dev2.dc1'
        )
        connected_device_2 = Device.objects.create(
            model=model,
            sn='sn_3',
            name='dev3.dc1'
        )
        connected_device_3 = Device.objects.create(
            model=model,
            sn='sn_4',
            name='dev4.dc1'
        )
        conn_1 = Connection.objects.create(
            connection_type=ConnectionType.network,
            outbound=master_device,
            inbound=connected_device_1
        )
        conn_2 = Connection.objects.create(
            connection_type=ConnectionType.network,
            outbound=master_device,
            inbound=connected_device_2
        )
        Connection.objects.create(
            connection_type=ConnectionType.network,
            outbound=master_device,
            inbound=connected_device_3
        )
        with mock.patch(
            'ralph.scan.postprocess.lldp_connections.get_device_data'
        ) as get_device_data_mock, mock.patch(
            'ralph.scan.postprocess.lldp_connections.merge_data'
        ) as merge_data_mock, mock.patch(
            'ralph.scan.postprocess.lldp_connections.append_merged_proposition'
        ) as append_merged_proposition_mock, mock.patch(
            'ralph.scan.postprocess.lldp_connections.select_data'
        ) as select_data_mock, mock.patch(
            'ralph.scan.postprocess.lldp_connections.'
            '_create_or_update_connection'
        ) as create_or_update_connection_mock:
            # we don't need sensible data here because we also mock method
            # which use this data...
            get_device_data_mock.return_value = {}
            merge_data_mock.return_value = {}
            append_merged_proposition_mock.return_value = {}
            # now we need sensible data...
            select_data_mock.return_value = {
                'connections': [
                    {
                        'connection_type': 'network',
                        'connected_device_serial_number': 'sn_2'
                    },
                    {
                        'connection_type': 'network',
                        'connected_device_serial_number': 'sn_3'
                    },
                    {
                        'connection_type': 'boo',
                        'connected_device_serial_number': 'xxx'
                    }
                ]
            }
            create_or_update_connection_mock.side_effect = [
                conn_1, conn_2, None
            ]
            # run it...
            _append_connections_to_device(master_device, {}, {})
        self.assertTrue(
            Connection.objects.filter(
                outbound=master_device,
                inbound=connected_device_1,
                connection_type=ConnectionType.network
            ).exists()
        )
        self.assertTrue(
            Connection.objects.filter(
                outbound=master_device,
                inbound=connected_device_2,
                connection_type=ConnectionType.network
            ).exists()
        )
        self.assertFalse(
            Connection.objects.filter(
                outbound=master_device,
                inbound=connected_device_3,
                connection_type=ConnectionType.network
            ).exists()
        )
