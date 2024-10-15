from ralph.data_center.publishers import _get_host_data
from ralph.security.tests.factories import SecurityScanFactory
from ralph.tests import RalphTestCase
from ralph.virtual.tests.factories import VirtualServerFactory


class PublisherTests(RalphTestCase):
    def test_get_host_data_after_deleting_securityscan(self):
        instance = VirtualServerFactory()
        security_scan = SecurityScanFactory(base_object=instance)
        old_hostname = instance.hostname
        instance.hostname = "hostname"
        instance.save()

        host_data = _get_host_data(instance)
        self.assertEqual(old_hostname, host_data["_previous_state"]["hostname"])
        self.assertEqual(instance.hostname, host_data["hostname"])
        self.assertEqual(
            security_scan.last_scan_date.strftime("%Y-%m-%dT%H:%M:%S"),
            host_data["securityscan"]["last_scan_date"],
        )
        self.assertEqual(
            security_scan.scan_status.name, host_data["securityscan"]["scan_status"]
        )

        instance.securityscan.delete()

        host_data = _get_host_data(instance)
        self.assertIsNone(host_data["securityscan"])
