from urllib.parse import urlencode

from django.test import TestCase
from django.urls import reverse

from ralph.admin.tests.admin_testcase import RalphAdminTestCase
from ralph.data_center.tests.factories import DataCenterAssetFactory
from ralph.switchports.models.validation import SwitchportDiffStatus, MISMATCH_STATUSES
from ralph.switchports.tests.factories import DiffEntryFactory, DiffStampFactory


class DiffDetectionTest(TestCase):
    pass


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
