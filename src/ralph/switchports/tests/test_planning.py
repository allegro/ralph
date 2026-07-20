from django.test import TestCase

from ralph.data_center.tests.factories import DataCenterAssetFactory
from ralph.switchports.connections.planning import switch_port_owner
from ralph.switchports.models import Connection, ConnectionMember, Port


class SwitchPortOwnerTestCase(TestCase):
    def setUp(self):
        self.switch = DataCenterAssetFactory(hostname="sw.owner.local")
        self.server_a = DataCenterAssetFactory(hostname="srv-a.local")
        self.server_b = DataCenterAssetFactory(hostname="srv-b.local")

    def _connect(self, switch_label, server, server_label="eth1"):
        switch_port = Port.objects.create(
            label=switch_label, data_center_asset=self.switch
        )
        server_port = Port.objects.create(
            label=server_label, data_center_asset=server
        )
        conn = Connection.objects.create()
        ConnectionMember.objects.create(connection=conn, port=switch_port)
        ConnectionMember.objects.create(connection=conn, port=server_port)
        return switch_port

    def test_nonexistent_port_has_no_owner(self):
        self.assertIsNone(
            switch_port_owner(self.switch, "0/0/30", self.server_b)
        )

    def test_unconnected_port_has_no_owner(self):
        Port.objects.create(label="0/0/30", data_center_asset=self.switch)
        self.assertIsNone(
            switch_port_owner(self.switch, "0/0/30", self.server_b)
        )

    def test_port_owned_by_another_asset(self):
        self._connect("0/0/30", self.server_a)
        self.assertEqual(
            switch_port_owner(self.switch, "0/0/30", self.server_b),
            self.server_a,
        )

    def test_port_owned_by_this_asset_is_not_a_conflict(self):
        self._connect("0/0/30", self.server_a)
        self.assertIsNone(
            switch_port_owner(self.switch, "0/0/30", self.server_a)
        )
