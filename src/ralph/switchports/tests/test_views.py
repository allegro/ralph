from django.test import TestCase
from django.urls import reverse

from ralph.accounts.tests.factories import UserFactory
from ralph.data_center.tests.factories import (
    DataCenterAssetFactory,
    RackFactory,
    RackModuleFactory,
)
from ralph.switchports.models import RackConfiguration, RackSwitchConfiguration


class RackSwitchportGridViewTest(TestCase):
    def setUp(self):
        self.client.force_login(UserFactory(is_staff=True, is_superuser=True))
        self.module = RackModuleFactory()
        self.rack = RackFactory(name="Rack B", rack_module=self.module)
        self.sibling = RackFactory(
            name="Rack A", rack_module=self.module, server_room=self.rack.server_room
        )
        self.url = reverse("admin:data_center_rack_switchport-grid", args=[self.rack.pk])

    def test_module_tabs_on_unconfigured_rack(self):
        RackFactory(rack_module=RackModuleFactory())
        RackFactory(rack_module=None)

        response = self.client.get(self.url)

        self.assertContains(response, "No switch configurations defined for this rack.")
        self.assertEqual(list(response.context["module_racks"]), [self.sibling, self.rack])
        self.assertContains(
            response,
            f'<a href="{self.url}" aria-current="page">{self.rack.name}</a>',
        )
        sibling_url = reverse("admin:data_center_rack_switchport-grid", args=[self.sibling.pk])
        self.assertContains(response, f'<a href="{sibling_url}">{self.sibling.name}</a>')
        sibling_response = self.client.get(sibling_url)
        self.assertContains(
            sibling_response,
            f'<a href="{sibling_url}" aria-current="page">{self.sibling.name}</a>',
        )

    def test_no_tabs_without_module(self):
        self.rack.rack_module = None
        self.rack.save(update_fields=["rack_module"])

        response = self.client.get(self.url)

        self.assertEqual(list(response.context["module_racks"]), [])
        self.assertNotContains(response, '<nav class="tabs rack-tabs"')

    def test_tabs_and_buttons_with_switch_configuration(self):
        rack_config, _ = RackConfiguration.objects.get_or_create(rack=self.rack)
        RackSwitchConfiguration.objects.create(
            rack_configuration=rack_config,
            switch=DataCenterAssetFactory(),
            label="eth1",
        )

        response = self.client.get(self.url)
        self.assertContains(response, "No assets found in this rack.")
        self.assertContains(response, '<nav class="tabs rack-tabs"')

        DataCenterAssetFactory(rack=self.rack, position=1)
        response = self.client.get(self.url)

        self.assertContains(response, '<nav class="tabs rack-tabs"')
        self.assertContains(
            response,
            '<button type="submit" class="grid-action">Save connections</button>',
        )
        self.assertContains(
            response,
            '<button type="submit" name="refresh_validation" class="grid-action btn-refresh">',
        )

    def test_highlight_query_parameter_marks_matching_asset_row(self):
        rack_config, _ = RackConfiguration.objects.get_or_create(rack=self.rack)
        RackSwitchConfiguration.objects.create(
            rack_configuration=rack_config,
            switch=DataCenterAssetFactory(),
            label="eth1",
        )
        asset = DataCenterAssetFactory(rack=self.rack, barcode="ASSET-TO-HIGHLIGHT")

        response = self.client.get(f"{self.url}?highlight={asset.barcode}")

        self.assertContains(response, '<tr class="row-highlighted">')
        self.assertTrue(response.context["rows"][0]["is_highlighted"])

    def test_highlight_query_parameter_does_not_mark_other_asset_rows(self):
        rack_config, _ = RackConfiguration.objects.get_or_create(rack=self.rack)
        RackSwitchConfiguration.objects.create(
            rack_configuration=rack_config,
            switch=DataCenterAssetFactory(),
            label="eth1",
        )
        DataCenterAssetFactory(rack=self.rack, barcode="OTHER-ASSET")

        response = self.client.get(f"{self.url}?highlight=UNKNOWN-ASSET")

        self.assertNotContains(response, 'class="row-highlighted"')
        self.assertFalse(response.context["rows"][0]["is_highlighted"])

    def test_highlight_query_parameter_marks_multiple_asset_rows(self):
        rack_config, _ = RackConfiguration.objects.get_or_create(rack=self.rack)
        RackSwitchConfiguration.objects.create(
            rack_configuration=rack_config,
            switch=DataCenterAssetFactory(),
            label="eth1",
        )
        first_asset = DataCenterAssetFactory(rack=self.rack, barcode="FIRST-ASSET")
        second_asset = DataCenterAssetFactory(rack=self.rack, barcode="SECOND-ASSET")

        response = self.client.get(
            f"{self.url}?highlight={first_asset.barcode},%20{second_asset.barcode}"
        )

        self.assertEqual(
            sum(row["is_highlighted"] for row in response.context["rows"]),
            2,
        )
