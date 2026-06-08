from io import StringIO
from tempfile import TemporaryDirectory

from django.core.management import call_command
from django.test import TestCase

from ralph.data_center.tests.factories import DataCenterAssetFactory
from ralph.switchports.models import Connection, ConnectionMember, Port


class GenerateSwitchportGraphCommandTestCase(TestCase):
    def setUp(self):
        self.switch = DataCenterAssetFactory(hostname="sw1.example.com")
        self.server = DataCenterAssetFactory(hostname="srv1.example.com")
        self.extra_host = DataCenterAssetFactory(hostname="srv2.example.com")

        self.switch_port = Port.objects.create(
            label="Gi0/1", data_center_asset=self.switch
        )
        self.server_port = Port.objects.create(
            label="eth0", data_center_asset=self.server
        )
        self.server_backup_port = Port.objects.create(
            label="eth1", data_center_asset=self.server
        )
        self.extra_port = Port.objects.create(
            label="eth1", data_center_asset=self.extra_host
        )

        self.connection = Connection.objects.create()
        ConnectionMember.objects.create(
            connection=self.connection, port=self.switch_port
        )
        ConnectionMember.objects.create(
            connection=self.connection, port=self.server_port
        )

        self.extra_connection = Connection.objects.create()
        ConnectionMember.objects.create(
            connection=self.extra_connection, port=self.server_backup_port
        )
        ConnectionMember.objects.create(
            connection=self.extra_connection, port=self.extra_port
        )

    def test_command_outputs_mermaid_graph(self):
        out = StringIO()

        call_command("generate_switchport_graph", stdout=out)

        output = out.getvalue()
        self.assertIn("graph LR", output)
        # nodes are per-hostname, not per-port
        self.assertIn("sw1.example.com", output)
        self.assertIn("srv1.example.com", output)
        # port names appear on the edge, not in the node label
        self.assertNotIn("sw1.example.com<br/>Gi0/1", output)
        # edge label contains both port names regardless of order
        self.assertTrue("Gi0/1" in output and "eth0" in output)
        # node ids are asset-based
        switch_id = f"asset_{self.switch.pk}"
        server_id = f"asset_{self.server.pk}"
        expected_edges = {
            f'{switch_id} <-->|"Gi0/1 ↔ eth0"| {server_id}',
            f'{server_id} <-->|"eth0 ↔ Gi0/1"| {switch_id}',
        }
        self.assertTrue(any(edge in output for edge in expected_edges))

    def test_same_hostname_single_node(self):
        """Two ports from the same asset share one node; both port names appear on separate edges."""
        out = StringIO()
        # server_backup_port (eth1) on self.server is connected to extra_host via extra_connection
        # self.server already appears in connection (eth0 ↔ Gi0/1) — should still be one node

        call_command("generate_switchport_graph", stdout=out)

        output = out.getvalue()
        # srv1.example.com must appear exactly once as a node definition
        self.assertEqual(output.count(f'asset_{self.server.pk}["srv1.example.com"]'), 1)

    def test_command_filters_connections_by_hostname(self):
        out = StringIO()

        call_command(
            "generate_switchport_graph",
            "--hostname=srv2.example.com",
            stdout=out,
        )

        output = out.getvalue()
        self.assertIn("srv2.example.com", output)
        self.assertIn("eth1", output)
        self.assertNotIn("sw1.example.com", output)
        self.assertNotIn("Gi0/1", output)

    def test_command_writes_graph_to_file(self):
        with TemporaryDirectory() as tmp_dir:
            output_path = f"{tmp_dir}/switchports.mmd"
            out = StringIO()

            call_command(
                "generate_switchport_graph",
                f"--output={output_path}",
                stdout=out,
            )

            with open(output_path, encoding="utf-8") as graph_file:
                saved_output = graph_file.read()

        self.assertIn("Saved graph to", out.getvalue())
        self.assertIn("graph LR", saved_output)
