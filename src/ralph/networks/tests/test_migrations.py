from django_migration_testcase import MigrationTest

from ralph.assets.models.components import Ethernet
from ralph.assets.tests.factories import EthernetFactory
from ralph.data_center.tests.factories import DataCenterAssetFactory


class RemoveBaseObjectTestCase(MigrationTest):
    before = [
        ('assets', '0012_auto_20160606_1409'),
        ('networks', '0002_add_ethernet_field'),
    ]

    after = [
        ('networks', '0003_custom_link_ips_to_eth'),
    ]

    def test_move_from_base_object_to_ethernet(self):
        IPAddress = self.get_model_before('networks.IPAddress')
        Ethernet = self.get_model_before('assets.Ethernet')
        BaseObject = self.get_model_before('assets.BaseObject')
        bo = BaseObject()
        bo.save()
        eth = Ethernet(base_object=bo)
        eth.save()
        ip = IPAddress(address='192.168.1.1', number=1, base_object_id=bo.pk)
        ip.ethernet_id = eth.pk
        ip.save()
        self.run_migration()

        IPAddress = self.get_model_after('networks.IPAddress')
        ip = IPAddress.objects.get(pk=ip.pk)
        self.assertEqual(ip.ethernet.pk, eth.pk)
