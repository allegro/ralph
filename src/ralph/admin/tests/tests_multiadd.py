# -*- coding: utf-8 -*-
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse

from ralph.admin.sites import ralph_site
from ralph.back_office.admin import BackOfficeAssetAdmin
from ralph.back_office.models import BackOfficeAsset
from ralph.back_office.tests.factories import BackOfficeAssetFactory
from ralph.data_center.models.physical import DataCenterAsset
from ralph.data_center.tests.factories import DataCenterAssetFactory
from ralph.tests.mixins import ClientMixin


class MultiAddTest(ClientMixin, TestCase):
    def setUp(self):  # noqa
        super().setUp()
        self.login_as_user()
        self.bo_admin = BackOfficeAssetAdmin(
            model=BackOfficeAsset, admin_site=ralph_site
        )
        self.dc_admin = BackOfficeAssetAdmin(
            model=DataCenterAsset, admin_site=ralph_site
        )
        self.bo_1 = BackOfficeAssetFactory()
        self.dc_1 = DataCenterAssetFactory(sn="12345")

    def tests_multi_add_bo(self):
        post_data = {
            "sn": "sn|sn2",
            "barcode": "barcode,barcode2",
            "imei": "990000862471854\n990000862471855",
        }
        response = self.client.post(
            reverse(self.bo_admin.get_url_name(), args=[self.bo_1.pk]),
            post_data,
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(BackOfficeAsset.objects.count(), 3)

        result = BackOfficeAsset.objects.filter(
            sn="sn", barcode="barcode", imei="990000862471854"
        ).count()
        self.assertEqual(result, 1)

    def test_multi_add_dc_with_not_required_field(self):
        post_data = {
            "sn": "dc_sn,dc_sn2",
            "barcode": "dc_barcode,dc_barcode2",
            "position": "1,2",
            "niw": "",
        }
        response = self.client.post(
            reverse(self.dc_admin.get_url_name(), args=[self.dc_1.pk]),
            post_data,
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(DataCenterAsset.objects.count(), 3)

        result = DataCenterAsset.objects.filter(
            sn="dc_sn",
            barcode="dc_barcode",
        ).count()
        self.assertEqual(result, 1)

    def test_multi_add_is_empty_field(self):
        post_data = {
            "sn": "dc_sn,dc_sn2",
            "barcode": "",
            "position": "1,2",
            "niw": "",
        }
        response = self.client.post(
            reverse(self.dc_admin.get_url_name(), args=[self.dc_1.pk]),
            post_data,
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(DataCenterAsset.objects.count(), 3)

    def test_multi_add_smaller_number_of_lines(self):
        post_data = {
            "sn": "dc_sn,dc_sn2",
            "barcode": "barcode",
            "position": "1,2",
            "niw": "",
        }
        response = self.client.post(
            reverse(self.dc_admin.get_url_name(), args=[self.dc_1.pk]),
            post_data,
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(DataCenterAsset.objects.count(), 3)

    def test_multi_add_duplicate_sn(self):
        post_data = {
            "sn": "dc_sn,dc_sn",
            "barcode": "barcode,barcode2",
            "position": "1,2",
            "niw": "",
        }
        response = self.client.post(
            reverse(self.dc_admin.get_url_name(), args=[self.dc_1.pk]),
            post_data,
            follow=True,
        )
        self.assertFormError(response, "form", "sn", "There are duplicates in field.")

    def test_multi_add_barcode_and_sn_empty(self):
        post_data = {
            "sn": "dc_sn,,dc_sn2",
            "barcode": "barcode,,barcode2",
            "position": "1,2,3",
            "niw": "",
        }
        response = self.client.post(
            reverse(self.dc_admin.get_url_name(), args=[self.dc_1.pk]),
            post_data,
            follow=True,
        )
        self.assertFormError(
            response, "form", "sn", "Fill at least on of sn,barcode in each row"
        )

    def test_multi_add_is_sn_exists(self):
        post_data = {
            "sn": self.dc_1.sn,
            "barcode": "barcode",
            "position": "1",
            "niw": "",
        }
        response = self.client.post(
            reverse(self.dc_admin.get_url_name(), args=[self.dc_1.pk]),
            post_data,
            follow=True,
        )
        self.assertFormError(
            response,
            "form",
            "sn",
            ("Following items already exist: " '<a href="{}">{}</a>').format(
                reverse(
                    "admin:data_center_datacenterasset_change", args=[self.dc_1.pk]
                ),
                self.dc_1.pk,
            ),
        )

    @override_settings(
        MULTIADD_DATA_CENTER_ASSET_FIELDS=[
            {"field": "sn", "allow_duplicates": False},
            {"field": "barcode", "allow_duplicates": False},
            {"field": "position", "allow_duplicates": True},
            {"field": "niw", "allow_duplicates": False},
        ]
    )
    def tests_multi_add_validation_integer(self):
        post_data = {
            "sn": "sn5",
            "barcode": "barcode5",
            "position": "string",
            "niw": "",
        }
        response = self.client.post(
            reverse(self.dc_admin.get_url_name(), args=[self.dc_1.pk]),
            post_data,
            follow=True,
        )
        self.assertFormError(response, "form", "position", "Enter a valid number.")
