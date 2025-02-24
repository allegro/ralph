from unittest.mock import patch

from ralph.data_center.tests.factories import DataCenterAssetFactory
from ralph.networks.models import IPAddress
from ralph.networks.receivers import update_dns_record
from ralph.networks.tests.factories import IPAddressFactory
from ralph.tests import RalphTestCase
from ralph.virtual.tests.factories import CloudHostFactory


class IPAddressReceiversTestCase(RalphTestCase):
    def setUp(self):
        self.cloud_ip = IPAddressFactory(ethernet__base_object=CloudHostFactory())
        # fetch "clean" ip from db to fet base object instead of final instance
        # (cloud host in this case)
        self.cloud_ip = IPAddress.objects.get(address=self.cloud_ip.address)
        self.dc_asset_ip = IPAddressFactory(
            ethernet__base_object=DataCenterAssetFactory()
        )
        self.dc_asset_ip = IPAddress.objects.get(address=self.dc_asset_ip.address)

    @patch("ralph.networks.receivers.DNSaaS")
    def test_should_not_send_event_to_dnsaas_when_nothing_is_changed(self, dnsaas_mock):
        update_dns_record(self.dc_asset_ip, False)
        dnsaas_mock.assert_not_called()
        dnsaas_mock().send_ipaddress_data.assert_not_called()

    @patch("ralph.networks.receivers.DNSaaS")
    def test_should_not_send_event_to_dnsaas_when_cloud_host(self, dnsaas_mock):
        self.dc_asset_ip.hostname = "myhost.mydc.net"
        update_dns_record(self.cloud_ip, False)
        dnsaas_mock.assert_not_called()
        dnsaas_mock().send_ipaddress_data.assert_not_called()

    @patch("ralph.networks.receivers.DNSaaS")
    def test_should_send_event_to_dnsaas_when_asset(self, dnsaas_mock):
        old_hostname = self.dc_asset_ip.hostname
        self.dc_asset_ip.hostname = "myhost.mydc.net"
        update_dns_record(self.dc_asset_ip, False)
        dnsaas_mock().send_ipaddress_data.assert_called_with(
            {
                "action": "update",
                "old": {
                    "address": self.dc_asset_ip.address,
                    "hostname": old_hostname,
                },
                "new": {
                    "address": self.dc_asset_ip.address,
                    "hostname": "myhost.mydc.net",
                },
                "service_uid": self.dc_asset_ip.ethernet.base_object.service.uid,
            }
        )
