from decimal import Decimal

from ddt import data, ddt, unpack
from django.core.urlresolvers import reverse
from django.db import connections
from django.test import RequestFactory, TestCase
from django.test.utils import CaptureQueriesContext

from ralph.accounts.tests.factories import UserFactory
from ralph.admin import ralph_site
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
            reverse('admin:{}_{}_export'.format(
                model._meta.app_label, model._meta.model_name
            )),
            filters
        )
        request.user = self.user

        file_format = RawFormat()
        queryset = admin_class.get_export_queryset(request)
        export_data = admin_class.get_export_data(file_format, queryset)
        return export_data

    def _init(self, num=10):
        pass

    def _test_queries_count(self, func, nums=(10, 20), max_queries=10):
        # usually here we cannot specify exact number of queries since there is
        # a lot of dependencies (permissions etc), so we're going to check if
        # the number of queries do not change if the number of created objects
        # change
        queries_counts = set()
        for num in nums:
            self._init(num)
            with CaptureQueriesContext(connections['default']) as cqc:
                func()
                queries_counts.add(len(cqc))
        self.assertEqual(
            len(queries_counts),
            1,
            msg='Different queries count: {}'.format(queries_counts)
        )
        self.assertLessEqual(queries_counts.pop(), max_queries)


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
        for i, dca in enumerate(self.data_center_assets, start=num * 2):
            dca.parent = DataCenterAssetFullFactory()
            dca.parent.management_ip = '10.20.30.{}'.format(i)
            dca.save()
            self.data_center_assets_map[dca.id] = dca
            self.data_center_assets_map[dca.parent.id] = dca.parent

    def test_data_center_asset_export(self):
        self._init(10)
        export_data = self._export(DataCenterAsset)
        # check if management ip is properly exported
        self.assertNotEqual(export_data.dict[0]['management_ip'], '')

    def test_data_center_asset_export_with_parent_queries_count(self):
        self._test_queries_count(func=lambda: self._export(
            DataCenterAsset
        ))

    def test_data_center_asset_export_with_parent(self):
        self._init(10)
        export_data = self._export(
            DataCenterAsset, filters={'parent__isnull': False}
        )
        # check if parent management ip is properly exported
        self.assertNotEqual(export_data.dict[0]['parent_management_ip'], '')
        dca_0_parent = self.data_center_assets_map[
            int(export_data.dict[0]['parent'])
        ]
        self.assertEqual(export_data.dict[0]['parent_str'], str(dca_0_parent))


@ddt
class BaseObjectsSupportExporterTestCase(SimulateAdminExportTestCase):

    def test_support_export_works_with_support_without_price(self):
        support = SupportFactory(price=None)
        BaseObjectsSupportFactory(support=support)
        export_data = self._export(BaseObjectsSupport)
        self.assertEqual(export_data.dict[0]['support__price'], '')
        self.assertEqual(
            export_data.dict[0]['support__price_per_object'], '0.00'
        )

    @unpack
    @data(
        (Decimal('11477.95'), 11, Decimal('1043.45')),
        (Decimal('10000'), 1, Decimal('10000.00')),
        (Decimal('0.0'), 100, Decimal('0.00'))
    )
    def test_get_content_type_for_model(
        self, support_price, objects_count, expected_price
    ):
        support = SupportFactory(price=support_price)
        BaseObjectsSupportFactory.create_batch(objects_count, support=support)
        export_data = self._export(BaseObjectsSupport)
        self.assertEqual(
            export_data.dict[0]['support__price_per_object'],
            str(expected_price)
        )
