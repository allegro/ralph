from unittest.mock import patch

from django.test import TestCase
from django.utils.translation import gettext as _

from ..templatetags.dashboard_tags import (
    get_user_equipment_to_accept_loan_tile_data,
    get_user_equipment_to_accept_return_tile_data,
    get_user_equipment_to_accept_tile_data,
    get_user_simcard_to_accept_tile_data
)


class TestTemplatetags(TestCase):
    @patch("ralph.admin.templatetags.dashboard_tags.get_acceptance_url")
    @patch("ralph.admin.templatetags.dashboard_tags.get_assets_to_accept")
    def test_hardware_release_label(self, mocked_gata, mocked_gau):
        mocked_gata().count.return_value = 1
        mocked_gau.return_value = "boo"
        ret = get_user_equipment_to_accept_tile_data(None)
        assert ret["label"] == _("Hardware pick up")

    @patch("ralph.admin.templatetags.dashboard_tags.get_loan_acceptance_url")
    @patch("ralph.admin.templatetags.dashboard_tags.get_assets_to_accept_loan")
    def test_hardware_loan_label(self, mocked_gatal, mocked_glau):
        mocked_gatal().count.return_value = 1
        mocked_glau.return_value = "boo"
        ret = get_user_equipment_to_accept_loan_tile_data(None)
        assert ret["label"] == _("Hardware loan")

    @patch("ralph.admin.templatetags.dashboard_tags.get_return_acceptance_url")
    @patch("ralph.admin.templatetags.dashboard_tags.get_assets_to_accept_return")  # noqa:
    def test_hardware_return_label(self, mocked_gatar, mocked_grau):
        mocked_gatar().count.return_value = 1
        mocked_grau.return_value = "boo"
        ret = get_user_equipment_to_accept_return_tile_data(None)
        assert ret["label"] == _("Hardware return")

    @patch("ralph.admin.templatetags.dashboard_tags.get_simcard_acceptance_url")
    @patch("ralph.admin.templatetags.dashboard_tags.get_simcards_to_accept")
    def test_simcard_release_label(self, mocked_gata, mocked_gau):
        mocked_gata().count.return_value = 1
        mocked_gau.return_value = "boo"
        ret = get_user_simcard_to_accept_tile_data(None)
        self.assertEqual(ret["label"], _("SIM Card pick up"))
