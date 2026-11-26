from unittest import TestCase
from unittest.mock import Mock, patch

from django.urls import reverse

from ralph.api.tests._base import RalphAPITestCase
from ralph.virtual import cloudsync
from ralph.virtual.tests.factories import CloudProviderFactory


class TestLoadProcessors(TestCase):
    def setUp(self):
        self._drivers = cloudsync.CLOUD_SYNC_DRIVERS
        cloudsync.CLOUD_SYNC_DRIVERS = None

    def tearDown(self):
        cloudsync.CLOUD_SYNC_DRIVERS = self._drivers

    def test_loads_the_registered_entry_points(self):
        entry_point = Mock()
        entry_point.name = "proucessah"
        entry_point.load.return_value = "the processor"

        with patch.object(cloudsync, "entry_points", return_value=[entry_point]) as entry_points:
            cloudsync.load_processors()

        entry_points.assert_called_once_with(group=cloudsync.ENTRY_POINTS_GROUP)
        self.assertEqual({"proucessah": "the processor"}, cloudsync.CLOUD_SYNC_DRIVERS)

    def test_skips_entry_points_that_cannot_be_imported(self):
        broken = Mock()
        broken.name = "broken"
        broken.module = "no.such.module"
        broken.load.side_effect = ImportError
        working = Mock()
        working.name = "working"
        working.load.return_value = "the processor"

        with patch.object(cloudsync, "entry_points", return_value=[broken, working]):
            cloudsync.load_processors()

        self.assertEqual({"working": "the processor"}, cloudsync.CLOUD_SYNC_DRIVERS)


class TestCloudSyncRouter(RalphAPITestCase):
    def setUp(self):
        super().setUp()

        cloudsync.load_processors()

    def test_event_routed_correctly(self):
        processor_name = "proucessah"
        cloud_provider = CloudProviderFactory(
            cloud_sync_enabled=True, cloud_sync_driver=processor_name
        )

        cloudsync.CLOUD_SYNC_DRIVERS[processor_name] = Mock()
        test_data = {"test": True}

        url = reverse("cloud-sync-router", args=(cloud_provider.id,))
        self.client.post(url, test_data, format="json")

        cloudsync.CLOUD_SYNC_DRIVERS[processor_name].assert_called_once_with(
            cloud_provider, test_data
        )

    def test_404_bad_provider_id(self):
        bad_provider_id = 42

        url = reverse("cloud-sync-router", args=(bad_provider_id,))
        resp = self.client.post(url, {}, format="json")

        self.assertEqual(404, resp.status_code)

    def test_404_sync_disabled(self):
        cloud_provider = CloudProviderFactory(cloud_sync_enabled=False)

        url = reverse("cloud-sync-router", args=(cloud_provider.id,))
        resp = self.client.post(url, {}, format="json")

        self.assertEqual(404, resp.status_code)

    def test_404_processor_not_set(self):
        cloud_provider = CloudProviderFactory(cloud_sync_enabled=True, cloud_sync_driver=None)

        url = reverse("cloud-sync-router", args=(cloud_provider.id,))
        resp = self.client.post(url, {}, format="json")

        self.assertEqual(404, resp.status_code)

    def test_400_bad_json(self):
        processor_name = "proucessah"
        cloud_provider = CloudProviderFactory(
            cloud_sync_enabled=True, cloud_sync_driver=processor_name
        )

        cloudsync.CLOUD_SYNC_DRIVERS[processor_name] = Mock()
        test_data = None

        url = reverse("cloud-sync-router", args=(cloud_provider.id,))
        resp = self.client.post(url, test_data)

        self.assertEqual(400, resp.status_code)
        self.assertEqual(0, cloudsync.CLOUD_SYNC_DRIVERS[processor_name].call_count)

    def test_501_processor_not_available(self):
        cloud_provider = CloudProviderFactory(
            cloud_sync_enabled=True, cloud_sync_driver="CloudSyncProcessorFactory"
        )

        url = reverse("cloud-sync-router", args=(cloud_provider.id,))
        resp = self.client.post(url, {}, format="json")

        self.assertEqual(501, resp.status_code)
        self.assertEqual(b"Specified processor is not available", resp.content)
