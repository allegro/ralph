from ralph.assets.tests.factories import EthernetFactory
from ralph.data_center.publishers import _get_host_data

from ralph.tests import RalphTestCase
from ralph.virtual.tests.factories import VirtualServerFactory


class PublisherTests(RalphTestCase):
    def test_get_host_data_after_deleting_ethernet(self):
        instance = VirtualServerFactory()
        ethernet = EthernetFactory(base_object=instance)
        old_hostname = instance.hostname
        instance.hostname = "hostname"
        instance.save()

        host_data = _get_host_data(instance)
        self.assertEqual(old_hostname, host_data["_previous_state"]["hostname"])
        self.assertEqual(instance.hostname, host_data["hostname"])
        self.assertEqual(
            ethernet.mac.upper(),
            host_data["ethernet"][0]["mac"],
        )

        ethernet.delete()

        host_data = _get_host_data(instance)
        self.assertEqual([], host_data["ethernet"])
