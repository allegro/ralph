from datetime import datetime, timedelta

from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.urls import reverse

from ralph.api.tests._base import RalphAPITestCase
from ralph.data_center.models import BaseObjectCluster, Cluster, DataCenterAsset
from ralph.data_center.tests.factories import (
    ClusterFactory,
    DataCenterAssetFactory,
    DataCenterAssetFullFactory,
)
from ralph.data_center.views import RelationsView
from ralph.tests.mixins import ClientMixin
from ralph.virtual.models import CloudHost, VirtualServer
from ralph.virtual.tests.factories import (
    CloudHostFactory,
    CloudHostFullFactory,
    VirtualServerFactory,
    VirtualServerFullFactory,
)


def tomorrow():
    return datetime.now() + timedelta(days=1)


def yesterday():
    return datetime.now() + timedelta(days=-1)


class DataCenterAssetViewTest(ClientMixin, TestCase):
    def test_changelist_view(self):
        self.login_as_user()
        DataCenterAssetFullFactory.create_batch(10)
        with self.assertNumQueries(24):
            self.client.get(
                reverse("admin:data_center_datacenterasset_changelist"),
            )


class DCHostViewTest(ClientMixin, RalphAPITestCase):
    def setUp(self):
        self.login_as_user()

    def test_changelist_view(self):
        DataCenterAssetFullFactory.create_batch(5)
        VirtualServerFullFactory.create_batch(5)
        CloudHostFullFactory.create_batch(4)
        ClusterFactory.create_batch(4)
        with self.assertQueriesMoreOrLess(18, plus_minus=3):
            result = self.client.get(
                reverse("admin:data_center_dchost_changelist"),
            )
        # DCAssets - 5
        # VirtualServer + hypervisors - 10
        # Cluster - 4
        # CloudHost + hypervisors - 8
        self.assertEqual(result.context_data["cl"].result_count, 27)

    def test_changelist_datacenterasset_location(self):
        DataCenterAssetFullFactory(
            rack__name="Rack #1",
            rack__server_room__name="SR1",
            rack__server_room__data_center__name="DC1",
        )
        result = self.client.get(
            reverse("admin:data_center_dchost_changelist"),
        )
        self.assertContains(result, "DC1 / SR1 / Rack #1")

    def test_changelist_virtualserver_location(self):
        VirtualServerFullFactory(
            parent=DataCenterAssetFullFactory(
                rack__name="Rack #1",
                rack__server_room__name="SR1",
                rack__server_room__data_center__name="DC1",
                hostname="s12345.mydc.net",
            )
        )
        result = self.client.get(
            reverse("admin:data_center_dchost_changelist"),
        )
        self.assertContains(result, "DC1 / SR1 / Rack #1 / s12345.mydc.net")

    def test_changelist_cloudhost_location(self):
        CloudHostFullFactory(
            hypervisor=DataCenterAssetFullFactory(
                rack__name="Rack #1",
                rack__server_room__name="SR1",
                rack__server_room__data_center__name="DC1",
                hostname="s12345.mydc.net",
            )
        )
        result = self.client.get(
            reverse("admin:data_center_dchost_changelist"),
        )
        self.assertContains(result, "DC1 / SR1 / Rack #1 / s12345.mydc.net")

    def test_changelist_cluster_location(self):
        cluster = ClusterFactory()
        cluster.baseobjectcluster_set.create(
            is_master=True,
            base_object=DataCenterAssetFullFactory(
                rack__name="Rack #1",
                rack__server_room__name="SR1",
                rack__server_room__data_center__name="DC1",
            ),
        )
        result = self.client.get(
            reverse("admin:data_center_dchost_changelist"),
        )
        self.assertContains(result, "DC1 / SR1 / Rack #1")


class RelationsViewTest(TestCase):
    def setUp(self):
        self.view = RelationsView()
        self.view.object = DataCenterAssetFactory()

    def test_should_add_cloud_hosts_to_dictionary(self):
        cloud_host = ContentType.objects.get_for_model(CloudHost)
        self.view.object.cloudhost_set.add(*CloudHostFactory.create_batch(4))
        related_objects = {}
        self.view._add_cloud_hosts(related_objects)
        content_type = {c_t.content_type for c_t in related_objects["cloud_hosts"]}

        self.assertEqual(4, len(related_objects["cloud_hosts"]))
        self.assertEqual(1, len(content_type))
        self.assertEqual(cloud_host, content_type.pop())

    def test_should_add_virtual_hosts_to_dictionary(self):
        virtual_server = ContentType.objects.get_for_model(VirtualServer)
        self.view.object.children.add(*VirtualServerFactory.create_batch(4))
        related_objects = {}
        self.view._add_virtual_hosts(related_objects)
        content_type = {c_t.content_type for c_t in related_objects["virtual_hosts"]}

        self.assertEqual(4, len(related_objects["virtual_hosts"]))
        self.assertEqual(1, len(content_type))
        self.assertEqual(virtual_server, content_type.pop())

    def test_should_add_physical_hosts_to_dictionary(self):
        physical_server = ContentType.objects.get_for_model(DataCenterAsset)
        self.view.object.children.add(*DataCenterAssetFactory.create_batch(4))
        related_objects = {}
        self.view._add_physical_hosts(related_objects)
        content_type = {c_t.content_type for c_t in related_objects["physical_hosts"]}

        self.assertEqual(4, len(related_objects["physical_hosts"]))
        self.assertEqual(1, len(content_type))
        self.assertEqual(physical_server, content_type.pop())

    def test_should_add_clusters_to_dictionary(self):
        cluster = ContentType.objects.get_for_model(Cluster)
        self.view.object.clusters.add(
            BaseObjectCluster(cluster=ClusterFactory()), bulk=False
        )
        related_objects = {}
        self.view._add_clusters(related_objects)
        content_type = related_objects["clusters"][0].content_type

        self.assertEqual(1, len(related_objects["clusters"]))
        self.assertEqual(cluster, content_type)
