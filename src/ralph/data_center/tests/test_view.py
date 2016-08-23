from django.core.urlresolvers import reverse
from django.test import TestCase

from ralph.data_center.tests.factories import (
    ClusterFactory,
    DataCenterAssetFullFactory
)
from ralph.tests.mixins import ClientMixin
from ralph.virtual.tests.factories import (
    CloudHostFullFactory,
    VirtualServerFullFactory
)


class DataCenterAssetViewTest(ClientMixin, TestCase):
    def test_changelist_view(self):
        self.login_as_user()
        DataCenterAssetFullFactory.create_batch(10)
        with self.assertNumQueries(18):
            self.client.get(
                reverse('admin:data_center_datacenterasset_changelist'),
            )


class DCHostViewTest(ClientMixin, TestCase):
    def setUp(self):
        self.login_as_user()

    def test_changelist_view(self):
        DataCenterAssetFullFactory.create_batch(5)
        VirtualServerFullFactory.create_batch(5)
        CloudHostFullFactory.create_batch(4)
        ClusterFactory.create_batch(4)
        with self.assertNumQueries(19):
            result = self.client.get(
                reverse('admin:data_center_dchost_changelist'),
            )
        # DCAssets - 5
        # VirtualServer + hypervisors - 10
        # Cluster - 4
        # CloudHost + hypervisors - 8
        self.assertEqual(result.context_data['cl'].result_count, 27)

    def test_changelist_datacenterasset_location(self):
        DataCenterAssetFullFactory(
            rack__name='Rack #1',
            rack__server_room__name='SR1',
            rack__server_room__data_center__name='DC1',
        )
        result = self.client.get(
            reverse('admin:data_center_dchost_changelist'),
        )
        self.assertContains(result, 'DC1 / SR1 / Rack #1')

    def test_changelist_virtualserver_location(self):
        VirtualServerFullFactory(
            parent=DataCenterAssetFullFactory(
                rack__name='Rack #1',
                rack__server_room__name='SR1',
                rack__server_room__data_center__name='DC1',
                hostname='s12345.mydc.net',
            )
        )
        result = self.client.get(
            reverse('admin:data_center_dchost_changelist'),
        )
        self.assertContains(result, 'DC1 / SR1 / Rack #1 / s12345.mydc.net')

    def test_changelist_cloudhost_location(self):
        CloudHostFullFactory(
            hypervisor=DataCenterAssetFullFactory(
                rack__name='Rack #1',
                rack__server_room__name='SR1',
                rack__server_room__data_center__name='DC1',
                hostname='s12345.mydc.net',
            )
        )
        result = self.client.get(
            reverse('admin:data_center_dchost_changelist'),
        )
        self.assertContains(result, 'DC1 / SR1 / Rack #1 / s12345.mydc.net')

    def test_changelist_cluster_location(self):
        cluster = ClusterFactory()
        cluster.baseobjectcluster_set.create(
            is_master=True,
            base_object=DataCenterAssetFullFactory(
                rack__name='Rack #1',
                rack__server_room__name='SR1',
                rack__server_room__data_center__name='DC1',
            )
        )
        result = self.client.get(
            reverse('admin:data_center_dchost_changelist'),
        )
        self.assertContains(result, 'DC1 / SR1 / Rack #1')
