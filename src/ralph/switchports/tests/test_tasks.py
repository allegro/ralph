from unittest.mock import patch

from django.test import TestCase

from ralph.data_center.tests.factories import DataCenterAssetFactory, RackFactory
from ralph.switchports.models import (
    BackendValidationResult,
    RackConfiguration,
    RackSwitchConfiguration,
    RefreshJobStatus,
    SwitchportRefreshJob,
)
from ralph.switchports.sync.tasks import run_rack_refresh
from ralph.switchports.tests.helpers import make_interface, make_switch_dto


class _FakeLock:
    def acquire(self, *args, **kwargs):
        return True

    def release(self):
        return None


class _FakeRedis:
    def lock(self, *args, **kwargs):
        return _FakeLock()


class RunRackRefreshTaskTestCase(TestCase):
    def setUp(self):
        self.rack = RackFactory(name="TestRack-AsyncRefresh")
        self.switch_a = DataCenterAssetFactory(hostname="async.sw.a.local")
        self.switch_b = DataCenterAssetFactory(hostname="async.sw.b.local")
        self.server = DataCenterAssetFactory(
            hostname="async-srv.example.com", rack=self.rack, position=3
        )
        self.rack_config, _ = RackConfiguration.objects.get_or_create(rack=self.rack)
        self.sc_a = RackSwitchConfiguration.objects.create(
            rack_configuration=self.rack_config, switch=self.switch_a, label="eth1"
        )
        self.sc_b = RackSwitchConfiguration.objects.create(
            rack_configuration=self.rack_config, switch=self.switch_b, label="eth2"
        )

    def _switch_dto(self, hostname):
        return make_switch_dto(1, [make_interface("0/0/1", remote_name="")], hostname=hostname)

    @patch("ralph.switchports.sync.tasks.django_rq.get_connection")
    @patch("ralph.switchports.sync.tasks.NetmakerSwitchportBackend")
    def test_run_rack_refresh_success(self, MockBackend, mock_conn):
        mock_conn.return_value = _FakeRedis()
        backend = MockBackend.return_value
        backend.refresh_switch.return_value = {"success": True}
        backend.get_switchports.side_effect = lambda hostname, **kw: self._switch_dto(hostname)

        job = SwitchportRefreshJob.objects.create(
            rack_configuration=self.rack_config,
            status=RefreshJobStatus.PENDING,
        )

        with self.settings(SWITCHPORT_REFRESH_MAX_PARALLEL=1):
            run_rack_refresh(self.rack_config.id, job.id)

        job.refresh_from_db()
        self.assertEqual(job.status, RefreshJobStatus.SUCCESS)
        self.assertEqual(job.summary["refreshed_switches"], 2)
        self.assertIsNotNone(job.finished_at)
        # backend refresh triggered per switch, ports pulled into Ralph
        self.assertEqual(backend.refresh_switch.call_count, 2)
        self.assertTrue(BackendValidationResult.objects.filter(switch=self.switch_a).exists())
        self.assertTrue(BackendValidationResult.objects.filter(switch=self.switch_b).exists())

    @patch("ralph.switchports.sync.tasks.django_rq.get_connection")
    @patch("ralph.switchports.sync.tasks.NetmakerSwitchportBackend")
    def test_run_rack_refresh_records_switch_errors(self, MockBackend, mock_conn):
        mock_conn.return_value = _FakeRedis()
        backend = MockBackend.return_value
        backend.refresh_switch.side_effect = Exception("backend down")

        job = SwitchportRefreshJob.objects.create(
            rack_configuration=self.rack_config,
            status=RefreshJobStatus.PENDING,
        )

        with self.settings(SWITCHPORT_REFRESH_MAX_PARALLEL=1):
            run_rack_refresh(self.rack_config.id, job.id)

        job.refresh_from_db()
        self.assertEqual(job.status, RefreshJobStatus.ERROR)
        self.assertEqual(len(job.summary["errors"]), 2)
