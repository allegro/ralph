from django.core.urlresolvers import reverse
from django.db import connections
from django.test import RequestFactory, TestCase
from django.test.utils import CaptureQueriesContext

from ralph.accounts.tests.factories import UserFactory
from ralph.admin import ralph_site
from ralph.licences.models import Licence
from ralph.licences.tests.factories import (
    BackOfficeAssetLicenceFactory,
    DataCenterAssetLicenceFactory,
    LicenceFactory,
    LicenceUserFactory
)
from ralph.supports.models import Support
from ralph.supports.tests.factories import (
    BackOfficeAssetSupportFactory,
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
        self.assertLess(queries_counts.pop(), max_queries)


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

    def test_licence_export_queries_count(self):
        self._test_queries_count(func=lambda: self._export(Support))
