import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from django.test import TestCase, TransactionTestCase

from ralph.data_center.tests.factories import DataCenterAssetFactory
from ralph.switchports.connections import (
    ConnectionAlreadyExistsException,
    DefaultConnectionStrategy,
    NondestructiveConnectionStrategy,
    connect,
)
from ralph.switchports.models import Connection, ConnectionMember, Port
from ralph.switchports.tests.factories import PortFactory


class DefaultConnectionStrategyTest(TestCase):
    def setUp(self):
        self.strategy = DefaultConnectionStrategy()
        self.switch = DataCenterAssetFactory(hostname="sw1.example.com")
        self.server = DataCenterAssetFactory(hostname="srv1.example.com")
        self.port1 = Port.objects.create(label="Gi0/1", data_center_asset=self.switch)
        self.port2 = Port.objects.create(label="eth0", data_center_asset=self.server)

    def test_connect_two_unconnected_ports(self):
        connection, created = self.strategy.connect(self.port1, self.port2)

        self.assertTrue(created)
        self.assertEqual(Connection.objects.count(), 1)
        self.assertEqual(ConnectionMember.objects.count(), 2)
        ports = set(connection.members.values_list("port_id", flat=True))
        self.assertEqual(ports, {self.port1.id, self.port2.id})

    def test_connect_already_connected_ports_returns_existing(self):
        connection, created = self.strategy.connect(self.port1, self.port2)
        self.assertTrue(created)

        connection2, created2 = self.strategy.connect(self.port1, self.port2)

        self.assertFalse(created2)
        self.assertEqual(connection.id, connection2.id)
        self.assertEqual(Connection.objects.count(), 1)

    def test_connect_already_connected_ports_reverse_order(self):
        connection, _ = self.strategy.connect(self.port1, self.port2)

        connection2, created = self.strategy.connect(self.port2, self.port1)

        self.assertFalse(created)
        self.assertEqual(connection.id, connection2.id)

    def test_connect_replaces_existing_connection_on_port1(self):
        port3 = PortFactory(label="eth1", data_center_asset=self.server)
        self.strategy.connect(self.port1, port3)

        connection, created = self.strategy.connect(self.port1, self.port2)

        self.assertTrue(created)
        self.assertEqual(Connection.objects.count(), 1)
        ports = set(connection.members.values_list("port_id", flat=True))
        self.assertEqual(ports, {self.port1.id, self.port2.id})

    def test_connect_replaces_existing_connection_on_port2(self):
        port3 = PortFactory(label="eth1", data_center_asset=self.server)
        self.strategy.connect(self.port2, port3)

        connection, created = self.strategy.connect(self.port1, self.port2)

        self.assertTrue(created)
        self.assertEqual(Connection.objects.count(), 1)
        ports = set(connection.members.values_list("port_id", flat=True))
        self.assertEqual(ports, {self.port1.id, self.port2.id})

    def test_connect_replaces_existing_connections_on_both_ports(self):
        port3 = PortFactory(label="Gi0/2", data_center_asset=self.switch)
        port4 = PortFactory(label="eth1", data_center_asset=self.server)
        self.strategy.connect(self.port1, port3)
        self.strategy.connect(self.port2, port4)

        connection, created = self.strategy.connect(self.port1, self.port2)

        self.assertTrue(created)
        self.assertEqual(Connection.objects.count(), 1)
        ports = set(connection.members.values_list("port_id", flat=True))
        self.assertEqual(ports, {self.port1.id, self.port2.id})

    def test_connect_handles_orphaned_connection_without_members(self):
        orphan = Connection.objects.create()
        ConnectionMember.objects.create(connection=orphan, port=self.port1)

        connection, created = self.strategy.connect(self.port1, self.port2)

        self.assertTrue(created)
        self.assertEqual(Connection.objects.count(), 1)
        ports = set(connection.members.values_list("port_id", flat=True))
        self.assertEqual(ports, {self.port1.id, self.port2.id})


class NondestructiveConnectionStrategyTest(TestCase):
    def setUp(self):
        self.strategy = NondestructiveConnectionStrategy()
        self.switch = DataCenterAssetFactory(hostname="sw1.example.com")
        self.server = DataCenterAssetFactory(hostname="srv1.example.com")
        self.port1 = Port.objects.create(label="Gi0/1", data_center_asset=self.switch)
        self.port2 = Port.objects.create(label="eth0", data_center_asset=self.server)

    def test_connect_two_unconnected_ports(self):
        connection, created = self.strategy.connect(self.port1, self.port2)

        self.assertTrue(created)
        self.assertEqual(Connection.objects.count(), 1)
        self.assertEqual(ConnectionMember.objects.count(), 2)
        ports = set(connection.members.values_list("port_id", flat=True))
        self.assertEqual(ports, {self.port1.id, self.port2.id})

    def test_connect_already_connected_ports_returns_existing(self):
        connection, _ = self.strategy.connect(self.port1, self.port2)

        connection2, created = self.strategy.connect(self.port1, self.port2)

        self.assertFalse(created)
        self.assertEqual(connection.id, connection2.id)
        self.assertEqual(Connection.objects.count(), 1)

    def test_connect_already_connected_ports_reverse_order(self):
        connection, _ = self.strategy.connect(self.port1, self.port2)

        connection2, created = self.strategy.connect(self.port2, self.port1)

        self.assertFalse(created)
        self.assertEqual(connection.id, connection2.id)

    def test_raises_when_port1_already_connected_to_other_port(self):
        port3 = PortFactory(label="eth1", data_center_asset=self.server)
        self.strategy.connect(self.port1, port3)

        with self.assertRaises(ConnectionAlreadyExistsException):
            self.strategy.connect(self.port1, self.port2)

        self.assertEqual(Connection.objects.count(), 1)

    def test_raises_when_port2_already_connected_to_other_port(self):
        port3 = PortFactory(label="Gi0/2", data_center_asset=self.switch)
        self.strategy.connect(self.port2, port3)

        with self.assertRaises(ConnectionAlreadyExistsException):
            self.strategy.connect(self.port1, self.port2)

        self.assertEqual(Connection.objects.count(), 1)

    def test_raises_when_both_ports_already_connected_to_other_ports(self):
        port3 = PortFactory(label="Gi0/2", data_center_asset=self.switch)
        port4 = PortFactory(label="eth1", data_center_asset=self.server)
        self.strategy.connect(self.port1, port3)
        self.strategy.connect(self.port2, port4)

        with self.assertRaises(ConnectionAlreadyExistsException):
            self.strategy.connect(self.port1, self.port2)

        self.assertEqual(Connection.objects.count(), 2)


class ConnectFunctionTest(TestCase):
    def setUp(self):
        self.switch = DataCenterAssetFactory(hostname="sw1.example.com")
        self.server = DataCenterAssetFactory(hostname="srv1.example.com")
        self.port1 = Port.objects.create(label="Gi0/1", data_center_asset=self.switch)
        self.port2 = Port.objects.create(label="eth0", data_center_asset=self.server)

    def test_connect_uses_default_strategy(self):
        connection, created = connect(self.port1, self.port2)

        self.assertTrue(created)
        self.assertEqual(Connection.objects.count(), 1)

    def test_connect_with_explicit_strategy(self):
        strategy = NondestructiveConnectionStrategy()

        connection, created = connect(self.port1, self.port2, strategy=strategy)

        self.assertTrue(created)
        self.assertEqual(Connection.objects.count(), 1)


class DefaultConnectionStrategyConcurrencyTest(TransactionTestCase):
    def setUp(self):
        self.switch = DataCenterAssetFactory(hostname="sw1.example.com")
        self.server = DataCenterAssetFactory(hostname="srv1.example.com")
        self.server2 = DataCenterAssetFactory(hostname="srv2.example.com")
        self.port1 = Port.objects.create(label="Gi0/1", data_center_asset=self.switch)
        self.port2 = Port.objects.create(label="eth0", data_center_asset=self.server)
        self.port3 = Port.objects.create(label="eth0", data_center_asset=self.server2)

    def test_concurrent_connects_to_same_port_results_in_single_connection(self):
        """
        Two threads race to connect different ports to port1.
        After both finish, port1 should have exactly one connection.
        """
        strategy = DefaultConnectionStrategy()
        barrier = threading.Barrier(2, timeout=5)

        def connect_with_barrier(port_a, port_b):
            barrier.wait()
            return strategy.connect(port_a, port_b)

        with ThreadPoolExecutor(max_workers=2) as executor:
            future1 = executor.submit(connect_with_barrier, self.port1, self.port2)
            future2 = executor.submit(connect_with_barrier, self.port1, self.port3)

            for f in as_completed([future1, future2]):
                f.result()

        connections = Connection.objects.filter(members__port=self.port1)
        self.assertEqual(connections.count(), 1)
        connection = connections.get()
        member_ports = set(connection.members.values_list("port_id", flat=True))
        self.assertIn(self.port1.id, member_ports)
        self.assertEqual(len(member_ports), 2)


class NondestructiveConnectionStrategyConcurrencyTest(TransactionTestCase):
    def setUp(self):
        self.switch = DataCenterAssetFactory(hostname="sw1.example.com")
        self.server = DataCenterAssetFactory(hostname="srv1.example.com")
        self.server2 = DataCenterAssetFactory(hostname="srv2.example.com")
        self.port1 = Port.objects.create(label="Gi0/1", data_center_asset=self.switch)
        self.port2 = Port.objects.create(label="eth0", data_center_asset=self.server)
        self.port3 = Port.objects.create(label="eth0", data_center_asset=self.server2)

    def test_concurrent_connects_to_same_port_one_succeeds_one_fails(self):
        """
        Two threads race to connect different ports to port1 using nondestructive strategy.
        Exactly one should succeed and one should raise ConnectionAlreadyExistsException.
        """
        strategy = NondestructiveConnectionStrategy()
        barrier = threading.Barrier(2, timeout=5)

        def connect_with_barrier(port_a, port_b):
            barrier.wait()
            return strategy.connect(port_a, port_b)

        with ThreadPoolExecutor(max_workers=2) as executor:
            future1 = executor.submit(connect_with_barrier, self.port1, self.port2)
            future2 = executor.submit(connect_with_barrier, self.port1, self.port3)

            results = []
            exceptions = []
            for f in as_completed([future1, future2]):
                try:
                    results.append(f.result())
                except ConnectionAlreadyExistsException:
                    exceptions.append(True)

        self.assertEqual(len(results), 1)
        self.assertEqual(len(exceptions), 1)
        self.assertEqual(Connection.objects.count(), 1)
