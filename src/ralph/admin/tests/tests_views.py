# -*- coding: utf-8 -*-
from importlib import import_module

from ddt import ddt, data, unpack
from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import connections
from django.test import RequestFactory, TestCase
from django.test.utils import CaptureQueriesContext

from ralph.admin.sites import ralph_site


FACTORY_MAP = {
    'auth.Group': 'accounts.GroupFactory',
    'accounts.RalphUser': 'UserFactory',
    'accounts.Region': 'RegionFactory',
    'accounts.Team': 'TeamFactory',
    'assets.AssetHolder': 'AssetHolderFactory',
    'assets.AssetModel': 'BackOfficeAssetModelFactory',
    'assets.BudgetInfo': 'BudgetInfoFactory',
    'assets.BusinessSegment': 'BusinessSegmentFactory',
    'assets.Category': 'CategoryFactory',
    'assets.Environment': 'EnvironmentFactory',
    'assets.Manufacturer': 'ManufacturerFactory',
    'assets.ProfitCenter': 'ProfitCenterFactory',
    'assets.Service': 'ServiceFactory',
    'assets.ServiceEnvironment': 'ServiceEnvironmentFactory',
    'assets.BaseObject': 'BaseObjectFactory',
    'assets.ComponentModel': 'ComponentModelFactory',
    'assets.Ethernet': 'EthernetFactory',
    'assets.ConfigurationClass': 'ConfigurationClassFactory',
    'assets.ConfigurationModule': 'ConfigurationModuleFactory',
    'back_office.BackOfficeAsset': 'BackOfficeAssetFactory',
    'back_office.OfficeInfrastructure': 'OfficeInfrastructureFactory',
    'back_office.Warehouse': 'WarehouseFactory',
    'dashboards.Dashboard': 'DashboardFactory',
    'dashboards.Graph': 'GraphFactory',
    'data_center.DiskShare': 'DiskShareFactory',
    'data_center.DiskShareMount': 'DiskShareMountFactory',
    'data_center.DCHost': 'DataCenterAssetFullFactory',
    'data_center.Accessory': 'AccessoryFactory',
    'data_center.DataCenter': 'DataCenterFactory',
    'data_center.DataCenterAsset': 'DataCenterAssetFullFactory',
    'data_center.Rack': 'RackFactory',
    'data_center.RackAccessory': 'RackAccessoryFactory',
    'data_center.ServerRoom': 'ServerRoomFactory',
    'data_center.Cluster': 'ClusterFactory',
    'data_center.ClusterType': 'ClusterTypeFactory',
    'data_center.Database': 'DatabaseFactory',
    'data_center.VIP': 'VIPFactory',
    'deployment.Preboot': 'PrebootFactory',
    'deployment.PrebootConfiguration': 'PrebootConfigurationFactory',
    'dhcp.DHCPServer': 'DHCPServerFactory',
    'dhcp.DNSServer': 'DNSServerFactory',
    'domains.Domain': 'DomainFactory',
    'domains.DomainContract': 'DomainContractFactory',
    'domains.DomainRegistrant': 'DomainRegistrantFactory',
    'licences.Licence': 'LicenceFactory',
    'licences.LicenceType': 'LicenceTypeFactory',
    'licences.Software': 'SoftwareFactory',
    # TODO: add missing factory
    # networks.DiscoveryQueue': 'DiscoveryQueueFactory',
    'networks.IPAddress': 'IPAddressFactory',
    'networks.NetworkEnvironment': 'NetworkEnvironmentFactory',
    'networks.NetworkKind': 'NetworkKindFactory',
    'operations.Change': 'ChangeFactory',
    'operations.Failure': 'FailureFactory',
    'operations.Incident': 'IncidentFactory',
    'operations.Operation': 'OperationFactory',
    'operations.OperationType': 'OperationTypeFactory',
    'operations.Problem': 'ProblemFactory',
    'reports.Report': 'ReportFactory',
    'reports.ReportLanguage': 'ReportLanguageFactory',
    'supports.Support': 'SupportFactory',
    'supports.SupportType': 'SupportTypeFactory',
    'virtual.CloudFlavor': 'CloudFlavorFactory',
    'virtual.CloudHost': 'CloudHostFullFactory',
    'virtual.CloudProject': 'CloudProjectFactory',
    'virtual.CloudProvider': 'CloudProviderFactory',
    'virtual.VirtualServer': 'VirtualServerFullFactory',
    'virtual.VirtualServerType': 'VirtualServerTypeFactory',
}

SQL_QUERY_LIMIT = 30


def _get_factory_from_path(app_label, factory_name):
    bits = factory_name.split('.')
    app = app_label
    if len(bits) == 2:
        app = bits[0]
        factory_name = bits[1]
    module_path = 'ralph.{}.tests.factories'.format(app)
    module = import_module(module_path)
    return getattr(module, factory_name)


def _get_model_and_factory_from_path(model_path, factory):
    app_label, model_name = model_path.split('.')
    model = apps.get_model(app_label, model_name)
    factory = _get_factory_from_path(app_label, factory)
    return model, factory


@ddt
class ViewsTest(TestCase):

    def setUp(self):
        self.request = RequestFactory().get('/')
        self.request.user = get_user_model().objects.create_superuser(
            'test', 'test@test.test', 'test'
        )
        self.request.session = {}

    @unpack
    @data(*FACTORY_MAP.items())
    def test_numbers_of_sql_query_and_response_status_is_200(self, model, factory):
        model, factory_model = _get_model_and_factory_from_path(model, factory)
        model_admin = ralph_site._registry[model]

        # Create 10 records:
        factory_model.create_batch(10)

        with CaptureQueriesContext(connections['default']) as cqc:
            change_list = model_admin.changelist_view(self.request)
            self.assertEqual(change_list.status_code, 200)
            query_count = len(cqc)

        # Create next 10 records:
        factory_model.create_batch(10)

        with CaptureQueriesContext(connections['default']) as cqc:
            change_list = model_admin.changelist_view(self.request)
            self.assertEqual(query_count, len(cqc))
            self.assertFalse(len(cqc) > SQL_QUERY_LIMIT)

        change_form = model_admin.changeform_view(
            self.request, object_id=None
        )
        self.assertEqual(change_form.status_code, 200)

    @unpack
    @data(*FACTORY_MAP.items())
    def test_variables(self, model, factory):
        model, factory_model = _get_model_and_factory_from_path(model, factory)
        model_admin = ralph_site._registry[model]
        obj = factory_model()
        change_list_response = model_admin.changelist_view(self.request)
        change_list_content = change_list_response.render().content
        self.assertFalse(
            settings.TEMPLATE_STRING_IF_INVALID in str(change_list_content)
        )
        changeform_view_response = model_admin.changeform_view(
            self.request, str(obj.pk)
        )
        changeform_view_content = changeform_view_response.render().content
        self.assertFalse(
            settings.TEMPLATE_STRING_IF_INVALID in str(change_list_content)
        )
