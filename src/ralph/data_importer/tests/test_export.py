from decimal import Decimal

from ddt import data, ddt, unpack
from django.db import connections
from django.test import RequestFactory, TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from ralph.accounts.tests.factories import UserFactory
from ralph.admin.sites import ralph_site
from ralph.data_center.models import DataCenterAsset
from ralph.data_center.tests.factories import DataCenterAssetFullFactory
from ralph.licences.models import Licence
from ralph.licences.tests.factories import (
    BackOfficeAssetLicenceFactory,
    DataCenterAssetLicenceFactory,
    LicenceFactory,
    LicenceUserFactory
)
from ralph.supports.models import BaseObjectsSupport, Support
from ralph.supports.tests.factories import (
    BackOfficeAssetSupportFactory,
    BaseObjectsSupportFactory,
    DataCenterAssetSupportFactory,
    SupportFactory
)


class RawFormat(object):
    def export_data(self, data):
        return data


class SimulateAdminExportTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = UserFactory(is_superuser=True, is_staff=True)

    def _export(self, model, filters=None):
        filters = filters or {}
        admin_class = ralph_site._registry[model]
        request = RequestFactory().get(
            reverse(
                "admin:{}_{}_export".format(
                    model._meta.app_label, model._meta.model_name
                )
            ),
            filters,
        )
        request.user = self.user

        file_format = RawFormat()
        queryset = admin_class.get_export_queryset(request)
        export_data = admin_class.get_export_data(
            file_format, queryset, request=request
        )
        return export_data

    def _init(self, num=10):
        raise NotImplementedError()

    def _test_queries_count(self, func, nums=(10, 20), max_queries=10):
        # usually here we cannot specify exact number of queries since there is
        # a lot of dependencies (permissions etc), so we're going to check if
        # the number of queries do not change
        # when the number of created objects changes
        first, second = nums

        self._init(first)
        with CaptureQueriesContext(connections["default"]) as cqc:
            func()
            first_queries = len(cqc)

        self._init(second)
        with CaptureQueriesContext(connections["default"]) as cqc:
            func()
            second_queries = len(cqc)
        self.assertEqual(
            first_queries,
            second_queries,
            msg=f"Different queries count. First: {first_queries}, second {second_queries}",
        )
        self.assertLessEqual(second_queries, max_queries)


class LicenceExporterTestCase(SimulateAdminExportTestCase):
    def _init(self, num=10):
        self.licences = LicenceFactory.create_batch(num)
        for licence in self.licences:
            DataCenterAssetLicenceFactory.create_batch(3, licence=licence)
            BackOfficeAssetLicenceFactory.create_batch(2, licence=licence)
            LicenceUserFactory.create_batch(3, licence=licence)

    def test_licence_export_queries_count(self):
        self._test_queries_count(func=lambda: self._export(Licence))


class SupportExporterTestCase(SimulateAdminExportTestCase):
    def _init(self, num=10):
        self.supports = SupportFactory.create_batch(num)
        for support in self.supports:
            BackOfficeAssetSupportFactory.create_batch(3, support=support)
            DataCenterAssetSupportFactory.create_batch(2, support=support)

    def test_support_export_queries_count(self):
        self._test_queries_count(func=lambda: self._export(Support))


class DataCenterAssetExporterTestCase(SimulateAdminExportTestCase):
    def _init(self, num=10):
        self.data_center_assets = DataCenterAssetFullFactory.create_batch(num)
        self.data_center_assets_map = {}
        for dca in self.data_center_assets:
            self.data_center_assets_map[dca.id] = dca

    def test_data_center_asset_export_queries_count(self):
        self._test_queries_count(
            func=lambda: self._export(DataCenterAsset), max_queries=12
        )

    def test_data_center_asset_export_filtered(self):
        self._init(10)
        first_id = next(iter(self.data_center_assets_map.keys()))
        with CaptureQueriesContext(connections["default"]) as cqc:
            export_data = self._export(DataCenterAsset, filters={"id": first_id})
            queries = len(cqc)
        self.assertEqual(len(export_data.dict), 1)
        self.assertLessEqual(queries, 12)


class DataCenterAssetExporterTestCaseWithParent(DataCenterAssetExporterTestCase):
    def _init(self, num=10):
        self.data_center_assets = DataCenterAssetFullFactory.create_batch(num)
        self.data_center_assets_map = {}
        for i, dca in enumerate(self.data_center_assets, start=num * 2):
            dca.parent = DataCenterAssetFullFactory()
            dca.parent.management_ip = "10.20.30.{}".format(i)
            dca.save()
            self.data_center_assets_map[dca.id] = dca
            self.data_center_assets_map[dca.parent.id] = dca.parent

    def test_data_center_asset_export(self):
        self._init(10)
        export_data = self._export(DataCenterAsset)
        # check if management ip is properly exported
        self.assertNotEqual(export_data.dict[0]["management_ip"], "")

    def test_data_center_asset_export_with_parent_queries_count(self):
        self._test_queries_count(
            func=lambda: self._export(DataCenterAsset), max_queries=12
        )

    def test_data_center_asset_export_with_parent(self):
        self._init(10)
        export_data = self._export(DataCenterAsset, filters={"parent__isnull": False})

        dca_with_parent = next(dca for dca in export_data.dict if dca["parent"])
        dca_0_parent = self.data_center_assets_map[int(dca_with_parent["parent"])]
        # check if parent management ip is properly exported
        self.assertNotEqual(dca_with_parent["parent_management_ip"], "")
        self.assertEqual(
            dca_with_parent["parent_str"], dca_0_parent.baseobject_ptr._str_with_type
        )


@ddt
class BaseObjectsSupportExporterTestCase(SimulateAdminExportTestCase):
    def test_support_export_works_with_support_without_price(self):
        support = SupportFactory(price=None)
        BaseObjectsSupportFactory(support=support)
        export_data = self._export(BaseObjectsSupport)
        self.assertEqual(export_data.dict[0]["support__price"], "")
        self.assertEqual(export_data.dict[0]["support__price_per_object"], "0.00")

    @unpack
    @data(
        (Decimal("11477.95"), 11, Decimal("1043.45")),
        (Decimal("10000"), 1, Decimal("10000.00")),
        (Decimal("0.0"), 100, Decimal("0.00")),
    )
    def test_get_content_type_for_model(
        self, support_price, objects_count, expected_price
    ):
        support = SupportFactory(price=support_price)
        BaseObjectsSupportFactory.create_batch(objects_count, support=support)
        export_data = self._export(BaseObjectsSupport)
        self.assertEqual(
            export_data.dict[0]["support__price_per_object"], str(expected_price)
        )
