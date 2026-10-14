from urllib.parse import urlencode

from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from ralph.admin.tests.admin_testcase import RalphAdminTestCase
from ralph.data_center.tests.factories import (
    DataCenterAssetFactory,
    DataCenterAssetFullFactory,
    RackFactory,
)
from ralph.switchports.connections import connect
from ralph.switchports.models import (
    DiffEntry,
    Port,
    ValidationStatus,
)
from ralph.switchports.models.validation import MISMATCH_STATUSES, SwitchportDiffStatus
from ralph.switchports.report.diff_detection import compare, compare_all
from ralph.switchports.tests.factories import (
    BackendValidationResultFactory,
    DiffEntryFactory,
    DiffStampFactory,
    PortFactory,
    RackSwitchConfigurationFactory,
)


class DiffDetectionTest(TestCase):
    def setUp(self):
        self.rack = RackFactory()
        self.switch = DataCenterAssetFullFactory(rack=self.rack)
        self.server = DataCenterAssetFullFactory(rack=self.rack)
        self.other_server = DataCenterAssetFullFactory(rack=self.rack)
        self.rack_configuration = self.rack.rack_configuration
        self.switch_configuration = RackSwitchConfigurationFactory(
            rack_configuration=self.rack_configuration,
            switch=self.switch,
            label="eth1",
        )

    def connect_switch_port(self, asset):
        switch_port = PortFactory(label="0/0/10", data_center_asset=self.switch)
        asset_port = PortFactory(label="eth1", data_center_asset=asset)
        connect(switch_port, asset_port)

    def test_compare_returns_not_validated_when_switch_validation_is_disabled(self):
        self.switch_configuration.backend_validation = False
        self.switch_configuration.save()
        result = compare(BackendValidationResultFactory())

        self.assertEqual(result.status, SwitchportDiffStatus.NOT_VALIDATED.value)
        self.assertIsNone(result.ralph_asset)
        self.assertIsNone(result.netmaker_asset)

    def test_compare_returns_port_missing(self):
        result = compare(BackendValidationResultFactory())

        self.assertEqual(result.status, SwitchportDiffStatus.PORT_MISSING.value)
        self.assertIsNone(result.ralph_asset)
        self.assertIsNone(result.netmaker_asset)

    def test_compare_returns_netmaker_empty(self):
        Port.objects.create(label="0/0/10", data_center_asset=self.switch)
        result = compare(
            BackendValidationResultFactory(
                status=ValidationStatus.PORT_NOT_FOUND.value,
                remote_asset=None,
            )
        )

        self.assertEqual(result.status, SwitchportDiffStatus.NETMAKER_EMPTY.value)
        self.assertIsNone(result.ralph_asset)
        self.assertIsNone(result.netmaker_asset)

    def test_compare_returns_ralph_empty(self):
        Port.objects.create(label="0/0/10", data_center_asset=self.switch)
        result = compare(BackendValidationResultFactory())

        self.assertEqual(result.status, SwitchportDiffStatus.RALPH_EMPTY.value)
        self.assertIsNone(result.ralph_asset)
        self.assertEqual(result.netmaker_asset, self.server)

    def test_compare_returns_same_asset(self):
        self.connect_switch_port(self.server)
        result = compare(BackendValidationResultFactory())

        self.assertEqual(result.status, SwitchportDiffStatus.SAME_ASSET.value)
        self.assertEqual(result.ralph_asset, self.server)
        self.assertEqual(result.netmaker_asset, self.server)

    def test_compare_returns_asset_mismatch(self):
        self.connect_switch_port(self.other_server)
        result = compare(BackendValidationResultFactory())

        self.assertEqual(result.status, SwitchportDiffStatus.ASSET_MISMATCH.value)
        self.assertEqual(result.ralph_asset, self.other_server)
        self.assertEqual(result.netmaker_asset, self.server)

    def test_compare_all_creates_entries_and_deletes_unmatched_entries(self):
        validation_result = BackendValidationResultFactory()
        stale_entry = DiffEntryFactory(
            switch=self.other_server,
            label="stale",
            status=SwitchportDiffStatus.PORT_MISSING.value,
        )

        compare_all()

        entry = DiffEntry.objects.get(
            switch=self.switch,
            label=validation_result.port_label,
        )
        self.assertEqual(entry.status, SwitchportDiffStatus.PORT_MISSING.value)
        self.assertFalse(DiffEntry.objects.filter(id=stale_entry.id).exists())

    def test_compare_all_keeps_entry_when_only_non_asset_status_is_unchanged(self):
        validation_result = BackendValidationResultFactory()
        existing_entry = DiffEntryFactory(
            switch=self.switch,
            label=validation_result.port_label,
            status=SwitchportDiffStatus.PORT_MISSING.value,
            ralph_asset=self.other_server,
            netmaker_asset=self.server,
        )

        compare_all()

        existing_entry.refresh_from_db()
        self.assertEqual(existing_entry.status, SwitchportDiffStatus.PORT_MISSING.value)
        self.assertEqual(existing_entry.ralph_asset, self.other_server)
        self.assertEqual(existing_entry.netmaker_asset, self.server)

    def test_compare_all_replaces_entry_when_status_changes(self):
        validation_result = BackendValidationResultFactory()
        existing_entry = DiffEntryFactory(
            switch=self.switch,
            label=validation_result.port_label,
            status=SwitchportDiffStatus.PORT_MISSING.value,
        )
        Port.objects.create(label=validation_result.port_label, data_center_asset=self.switch)

        compare_all()

        self.assertFalse(DiffEntry.objects.filter(id=existing_entry.id).exists())
        entry = DiffEntry.objects.get(
            switch=self.switch,
            label=validation_result.port_label,
        )
        self.assertEqual(entry.status, SwitchportDiffStatus.RALPH_EMPTY.value)

    def test_compare_all_replaces_entry_when_assets_change(self):
        validation_result = BackendValidationResultFactory()
        self.connect_switch_port(self.server)
        existing_entry = DiffEntryFactory(
            switch=self.switch,
            label=validation_result.port_label,
            status=SwitchportDiffStatus.SAME_ASSET.value,
            ralph_asset=self.server,
            netmaker_asset=self.other_server,
        )

        compare_all()

        self.assertFalse(DiffEntry.objects.filter(id=existing_entry.id).exists())
        entry = DiffEntry.objects.get(
            switch=self.switch,
            label=validation_result.port_label,
        )
        self.assertEqual(entry.status, SwitchportDiffStatus.SAME_ASSET.value)
        self.assertEqual(entry.netmaker_asset, self.server)


class SwitchportReportAdminTest(RalphAdminTestCase):
    def setUp(self):
        super().setUp()
        self.switch = DataCenterAssetFactory()

    def admin_url(self, params: dict | None = None):
        url = reverse("admin:switchports_diffentry_changelist")
        if params:
            return url + f"?{urlencode(params)}"
        else:
            return url

    def test_unstamped_is_present(self):
        status = SwitchportDiffStatus.RALPH_EMPTY.value
        _ = DiffEntryFactory(switch=self.switch, status=status)
        qs = self.get_response_queryset(self.admin_url())
        self.assertCountEqual([status], [r.status for r in qs])

    def test_stamped_is_not_present(self):
        status = SwitchportDiffStatus.RALPH_EMPTY.value
        entry = DiffEntryFactory(switch=self.switch, status=status)
        DiffStampFactory(entry=entry, actor=self.user)
        qs = self.get_response_queryset(self.admin_url())
        self.assertQuerySetEqual(qs, [])

    def test_stamped_is_present_if_filter_set_to_all(self):
        status = SwitchportDiffStatus.RALPH_EMPTY.value
        entry = DiffEntryFactory(switch=self.switch, status=status)
        DiffStampFactory(entry=entry, actor=self.user)
        qs = self.get_response_queryset(self.admin_url(params={"stamp": "all"}))
        self.assertEqual(len(qs), 1)

    def test_mismatched_statuses_shown_by_default(self):
        for status, _ in SwitchportDiffStatus.choices:
            DiffEntryFactory(switch=self.switch, status=status)
        qs = self.get_response_queryset(self.admin_url())
        self.assertCountEqual({s for s in MISMATCH_STATUSES}, [r.status for r in qs])

    def _create_fully_populated_entries(self, count: int):
        """Create entries touching every relation rendered on the changelist.

        Each entry has a switch and both assets placed in a rack (links to the
        switchport grid need ``asset.rack``). Every other entry is stamped, so
        both branches of ``ack_by`` (``stamp.actor`` and missing stamp) are hit.
        """
        for i in range(count):
            entry = DiffEntryFactory(
                switch=DataCenterAssetFactory(rack=RackFactory()),
                status=SwitchportDiffStatus.ASSET_MISMATCH.value,
                ralph_asset=DataCenterAssetFactory(rack=RackFactory()),
                netmaker_asset=DataCenterAssetFactory(rack=RackFactory()),
            )
            if i % 2 == 0:
                DiffStampFactory(entry=entry, actor=self.user)

    def _capture_changelist_queries(self, url) -> CaptureQueriesContext:
        with CaptureQueriesContext(connection) as queries:
            response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        return queries

    def test_changelist_query_count_does_not_depend_on_number_of_entries(self):
        url = self.admin_url(params={"status": "all", "stamp": "all"})
        self._create_fully_populated_entries(3)
        # warm up per-process caches (content types etc.) so they don't skew counts
        self.client.get(url)

        baseline = self._capture_changelist_queries(url)
        self._create_fully_populated_entries(3)
        doubled = self._capture_changelist_queries(url)

        self.assertEqual(
            len(baseline),
            len(doubled),
            "Changelist query count grows with number of rows (N+1):\n{}\n\nvs\n\n{}".format(
                "\n".join(q["sql"] for q in baseline.captured_queries),
                "\n".join(q["sql"] for q in doubled.captured_queries),
            ),
        )
