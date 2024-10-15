# -*- coding: utf-8 -*-
from importlib import import_module

from ddt import data, ddt
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.db import connections
from django.test import RequestFactory, TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from ralph.admin.sites import ralph_site
from ralph.tests.models import Foo

FACTORY_MAP = {
    "django.contrib.auth.models.Group": "ralph.accounts.tests.factories.GroupFactory",  # noqa
    "ralph.accessories.models.Accessory": "ralph.accessories.tests.factories.AccessoryFactory",  # noqa
    "ralph.access_cards.models.AccessCard": "ralph.access_cards.tests.factories.AccessCardFactory",  # noqa
    "ralph.access_cards.models.AccessZone": "ralph.access_cards.tests.factories.AccessZoneFactory",  # noqa
    "ralph.accounts.models.RalphUser": "ralph.accounts.tests.factories.UserFactory",  # noqa
    "ralph.accounts.models.Region": "ralph.accounts.tests.factories.RegionFactory",  # noqa
    "ralph.accounts.models.Team": "ralph.accounts.tests.factories.TeamFactory",
    "ralph.assets.models.assets.AssetHolder": "ralph.assets.tests.factories.AssetHolderFactory",  # noqa
    "ralph.assets.models.assets.AssetModel": "ralph.assets.tests.factories.BackOfficeAssetModelFactory",  # noqa
    "ralph.assets.models.assets.BudgetInfo": "ralph.assets.tests.factories.BudgetInfoFactory",  # noqa
    "ralph.assets.models.assets.BusinessSegment": "ralph.assets.tests.factories.BusinessSegmentFactory",  # noqa
    "ralph.assets.models.assets.Category": "ralph.assets.tests.factories.CategoryFactory",  # noqa
    "ralph.assets.models.assets.Environment": "ralph.assets.tests.factories.EnvironmentFactory",  # noqa
    "ralph.assets.models.assets.Manufacturer": "ralph.assets.tests.factories.ManufacturerFactory",  # noqa
    "ralph.assets.models.assets.ManufacturerKind": "ralph.assets.tests.factories.ManufacturerKindFactory",  # noqa
    "ralph.assets.models.assets.ProfitCenter": "ralph.assets.tests.factories.ProfitCenterFactory",  # noqa
    "ralph.assets.models.assets.Service": "ralph.assets.tests.factories.ServiceFactory",  # noqa
    "ralph.assets.models.assets.ServiceEnvironment": "ralph.assets.tests.factories.ServiceEnvironmentFactory",  # noqa
    "ralph.assets.models.base.BaseObject": "ralph.assets.tests.factories.BaseObjectFactory",  # noqa
    "ralph.assets.models.components.ComponentModel": "ralph.assets.tests.factories.ComponentModelFactory",  # noqa
    "ralph.assets.models.components.Disk": "ralph.assets.tests.factories.DiskFactory",  # noqa
    "ralph.assets.models.components.Ethernet": "ralph.assets.tests.factories.EthernetFactory",  # noqa
    "ralph.assets.models.components.FibreChannelCard": "ralph.assets.tests.factories.FibreChannelCardFactory",  # noqa
    "ralph.assets.models.components.Memory": "ralph.assets.tests.factories.MemoryFactory",  # noqa
    "ralph.assets.models.components.Processor": "ralph.assets.tests.factories.ProcessorFactory",  # noqa
    "ralph.assets.models.configuration.ConfigurationClass": "ralph.assets.tests.factories.ConfigurationClassFactory",  # noqa
    "ralph.assets.models.configuration.ConfigurationModule": "ralph.assets.tests.factories.ConfigurationModuleFactory",  # noqa
    "ralph.back_office.models.BackOfficeAsset": "ralph.back_office.tests.factories.BackOfficeAssetFactory",  # noqa
    "ralph.back_office.models.OfficeInfrastructure": "ralph.back_office.tests.factories.OfficeInfrastructureFactory",  # noqa
    "ralph.back_office.models.Warehouse": "ralph.back_office.tests.factories.WarehouseFactory",  # noqa
    "ralph.dashboards.models.Dashboard": "ralph.dashboards.tests.factories.DashboardFactory",  # noqa
    "ralph.dashboards.models.Graph": "ralph.dashboards.tests.factories.GraphFactory",  # noqa
    "ralph.data_center.models.components.DiskShare": "ralph.data_center.tests.factories.DiskShareFactory",  # noqa
    "ralph.data_center.models.components.DiskShareMount": "ralph.data_center.tests.factories.DiskShareMountFactory",  # noqa
    "ralph.data_center.models.hosts.DCHost": "ralph.data_center.tests.factories.DataCenterAssetFullFactory",  # noqa
    "ralph.data_center.models.physical.Accessory": "ralph.data_center.tests.factories.AccessoryFactory",  # noqa
    "ralph.data_center.models.physical.DataCenter": "ralph.data_center.tests.factories.DataCenterFactory",  # noqa
    "ralph.data_center.models.physical.DataCenterAsset": "ralph.data_center.tests.factories.DataCenterAssetFullFactory",  # noqa
    "ralph.data_center.models.physical.Rack": "ralph.data_center.tests.factories.RackFactory",  # noqa
    "ralph.data_center.models.physical.RackAccessory": "ralph.data_center.tests.factories.RackAccessoryFactory",  # noqa
    "ralph.data_center.models.physical.ServerRoom": "ralph.data_center.tests.factories.ServerRoomFactory",  # noqa
    "ralph.data_center.models.virtual.BaseObjectCluster": "ralph.data_center.tests.factories.BaseObjectClusterFactory",  # noqa
    "ralph.data_center.models.virtual.Cluster": "ralph.data_center.tests.factories.ClusterFactory",  # noqa
    "ralph.data_center.models.virtual.ClusterType": "ralph.data_center.tests.factories.ClusterTypeFactory",  # noqa
    "ralph.data_center.models.virtual.Database": "ralph.data_center.tests.factories.DatabaseFactory",  # noqa
    "ralph.data_center.models.virtual.VIP": "ralph.data_center.tests.factories.VIPFactory",  # noqa
    "ralph.deployment.models.Preboot": "ralph.deployment.tests.factories.PrebootFactory",  # noqa
    "ralph.deployment.models.PrebootConfiguration": "ralph.deployment.tests.factories.PrebootConfigurationFactory",  # noqa
    "ralph.dhcp.models.DHCPServer": "ralph.dhcp.tests.factories.DHCPServerFactory",  # noqa
    "ralph.dhcp.models.DNSServer": "ralph.dhcp.tests.factories.DNSServerFactory",  # noqa
    "ralph.dhcp.models.DNSServerGroup": "ralph.dhcp.tests.factories.DNSServerGroupFactory",  # noqa
    "ralph.domains.models.domains.DNSProvider": "ralph.domains.tests.factories.DNSProviderFactory",  # noqa
    "ralph.domains.models.domains.Domain": "ralph.domains.tests.factories.DomainFactory",  # noqa
    "ralph.domains.models.domains.DomainCategory": "ralph.domains.tests.factories.DomainCategoryFactory",  # noqa
    "ralph.domains.models.domains.DomainContract": "ralph.domains.tests.factories.DomainContractFactory",  # noqa
    "ralph.domains.models.domains.DomainRegistrant": "ralph.domains.tests.factories.DomainRegistrantFactory",  # noqa
    "ralph.domains.models.domains.DomainProviderAdditionalServices": "ralph.domains.tests.factories.DomainProviderAdditionalServicesFactory",  # noqa
    "ralph.lib.custom_fields.models.CustomField": "ralph.lib.custom_fields.tests.factories.CustomFieldFactory",  # noqa
    "ralph.lib.transitions.models.Transition": "ralph.lib.transitions.tests.factories.TransitionFactory",  # noqa
    "ralph.lib.transitions.models.TransitionJob": "ralph.lib.transitions.tests.factories.TransitionJobFactory",  # noqa
    "ralph.lib.transitions.models.TransitionModel": "ralph.lib.transitions.tests.factories.TransitionModelFactory",  # noqa
    "ralph.lib.transitions.models.TransitionsHistory": "ralph.lib.transitions.tests.factories.TransitionsHistoryFactory",  # noqa
    "ralph.licences.models.Licence": "ralph.licences.tests.factories.LicenceFactory",  # noqa
    "ralph.licences.models.LicenceType": "ralph.licences.tests.factories.LicenceTypeFactory",  # noqa
    "ralph.licences.models.LicenceUser": "ralph.licences.tests.factories.LicenceUserFactory",  # noqa
    "ralph.licences.models.Software": "ralph.licences.tests.factories.SoftwareFactory",  # noqa
    "ralph.networks.models.networks.IPAddress": "ralph.networks.tests.factories.IPAddressFactory",  # noqa
    "ralph.networks.models.networks.Network": "ralph.networks.tests.factories.NetworkFactory",  # noqa
    "ralph.networks.models.networks.NetworkEnvironment": "ralph.networks.tests.factories.NetworkEnvironmentFactory",  # noqa
    "ralph.networks.models.networks.NetworkKind": "ralph.networks.tests.factories.NetworkKindFactory",  # noqa
    "ralph.operations.models.Change": "ralph.operations.tests.factories.ChangeFactory",  # noqa
    "ralph.operations.models.Failure": "ralph.operations.tests.factories.FailureFactory",  # noqa
    "ralph.operations.models.Incident": "ralph.operations.tests.factories.IncidentFactory",  # noqa
    "ralph.operations.models.Operation": "ralph.operations.tests.factories.OperationFactory",  # noqa
    "ralph.operations.models.OperationType": "ralph.operations.tests.factories.OperationTypeFactory",  # noqa
    "ralph.operations.models.Problem": "ralph.operations.tests.factories.ProblemFactory",  # noqa
    "ralph.operations.models.OperationStatus": "ralph.operations.tests.factories.OperationStatusFactory",  # noqa
    "ralph.reports.models.Report": "ralph.reports.factories.ReportFactory",
    "ralph.reports.models.ReportLanguage": "ralph.reports.factories.ReportLanguageFactory",  # noqa
    "ralph.ssl_certificates.models.SSLCertificate": "ralph.ssl_certificates.tests.factories.SSLCertificatesFactory",  # noqa
    "ralph.supports.models.BaseObjectsSupport": "ralph.supports.tests.factories.BaseObjectsSupportFactory",  # noqa
    "ralph.supports.models.Support": "ralph.supports.tests.factories.SupportFactory",  # noqa
    "ralph.supports.models.SupportType": "ralph.supports.tests.factories.SupportTypeFactory",  # noqa
    "ralph.trade_marks.models.TradeMark": "ralph.trade_marks.tests.factories.TradeMarkFactory",  # noqa
    "ralph.trade_marks.models.TradeMarksLinkedDomains": "ralph.trade_marks.tests.factories.TradeMarksLinkedDomainsFactory",  # noqa
    "ralph.trade_marks.models.UtilityModel": "ralph.trade_marks.tests.factories.UtilityModelFactory",  # noqa
    "ralph.trade_marks.models.UtilityModelLinkedDomains": "ralph.trade_marks.tests.factories.UtilityModelLinkedDomainsFactory",  # noqa
    "ralph.trade_marks.models.ProviderAdditionalMarking": "ralph.trade_marks.tests.factories.ProviderAdditionalMarkingFactory",  # noqa
    "ralph.trade_marks.models.TradeMarkCountry": "ralph.trade_marks.tests.factories.TradeMarkCountryFactory",  # noqa
    "ralph.trade_marks.models.TradeMarkRegistrarInstitution": "ralph.trade_marks.tests.factories.TradeMarkRegistrarInstitutionFactory",  # noqa
    "ralph.virtual.models.CloudFlavor": "ralph.virtual.tests.factories.CloudFlavorFactory",  # noqa
    "ralph.virtual.models.CloudHost": "ralph.virtual.tests.factories.CloudHostFullFactory",  # noqa
    "ralph.virtual.models.CloudImage": "ralph.virtual.tests.factories.CloudImageFactory",  # noqa
    "ralph.virtual.models.CloudProject": "ralph.virtual.tests.factories.CloudProjectFactory",  # noqa
    "ralph.virtual.models.CloudProvider": "ralph.virtual.tests.factories.CloudProviderFactory",  # noqa
    "ralph.virtual.models.VirtualServer": "ralph.virtual.tests.factories.VirtualServerFullFactory",  # noqa
    "ralph.virtual.models.VirtualServerType": "ralph.virtual.tests.factories.VirtualServerTypeFactory",  # noqa
    "ralph.security.models.Vulnerability": "ralph.security.tests.factories.VulnerabilityFactory",  # noqa
    "ralph.security.models.SecurityScan": "ralph.security.tests.factories.SecurityScanFactory",  # noqa
    "ralph.sim_cards.models.SIMCard": "ralph.sim_cards.tests.factories.SIMCardFactory",  # noqa
    "ralph.sim_cards.models.CellularCarrier": "ralph.sim_cards.tests.factories.CellularCarrierFactory",  # noqa
    "ralph.sim_cards.models.SIMCardFeatures": "ralph.sim_cards.tests.factories.SIMCardFeatureFactory",  # noqa
    "ralph.trade_marks.models.Design": "ralph.trade_marks.tests.factories.DesignFactory",  # noqa
    "ralph.trade_marks.models.Patent": "ralph.trade_marks.tests.factories.PatentFactory",  # noqa
}

EXCLUDE_MODELS = [
    "django.contrib.contenttypes.models.ContentType",
    "ralph.assets.models.assets.Asset",
    "ralph.assets.models.base.BaseObject",  # TODO: Add in the future
    "ralph.assets.models.components.GenericComponent",
    "ralph.data_center.models.physical.Connection",
    "ralph.deployment.models.Deployment",
    "ralph.deployment.models.PrebootFile",
    "ralph.deployment.models.PrebootItem",
    "ralph.lib.custom_fields.models.CustomField",
    "ralph.lib.transitions.models.TransitionModel",
    "ralph.networks.models.networks.DiscoveryQueue",
    "ralph.tests.models.Bar",
    "ralph.tests.models.Car",
    "ralph.tests.models.Car2",
    "ralph.tests.models.Foo",
    "ralph.tests.models.TestManufacturer",
    "ralph.tests.models.Order",
    "ralph.tests.models.PolymorphicTestModel",
]

EXCLUDE_ADD_VIEW = [
    "ralph.assets.models.base.BaseObject",
    "ralph.data_center.models.hosts.DCHost",
    "ralph.supports.models.BaseObjectsSupport",
]

SQL_QUERY_LIMIT = 30


@ddt
class ViewsTest(TestCase):
    def setUp(self):
        self.request = RequestFactory().get("/")
        self.request.user = get_user_model().objects.create_superuser(
            "test", "test@test.test", "test"
        )
        self.request.session = {}

        # fetch content types first
        ContentType.objects.get_for_models(*ralph_site._registry.keys())

    @data(*ralph_site._registry.keys())
    def test_numbers_of_sql_query_and_response_status_is_200(self, model):
        model_admin = ralph_site._registry[model]
        query_count = 0
        model_class_path = "{}.{}".format(model.__module__, model.__name__)
        if model_class_path in EXCLUDE_MODELS:
            return

        module_path, factory_class = FACTORY_MAP[model_class_path].rsplit(".", 1)
        module = import_module(module_path)
        factory_model = getattr(module, factory_class)

        # Create 10 records:
        factory_model.create_batch(10)

        with CaptureQueriesContext(connections["default"]) as cqc:
            change_list = model_admin.changelist_view(self.request)
            self.assertEqual(change_list.status_code, 200)
            query_count = len(cqc)

        # Create next 10 records:
        factory_model.create_batch(10)

        with CaptureQueriesContext(connections["default"]) as cqc2:
            change_list = model_admin.changelist_view(self.request)
            self.assertEqual(
                query_count,
                len(cqc2),
                "Different query count for {}: \n {} \nvs\n{}".format(
                    model_class_path,
                    "\n".join([q["sql"] for q in cqc.captured_queries]),
                    "\n".join([q["sql"] for q in cqc2.captured_queries]),
                ),
            )
            self.assertFalse(len(cqc2) > SQL_QUERY_LIMIT)

        if model_class_path not in EXCLUDE_ADD_VIEW:
            change_form = model_admin.changeform_view(self.request, object_id=None)
            self.assertEqual(change_form.status_code, 200)
        change_form = model_admin.changeform_view(
            self.request, object_id=str(model.objects.first().id)
        )
        self.assertEqual(change_form.status_code, 200)


class ViewMixinTest(TestCase):
    def setUp(self):
        password = "secret"
        self.user = get_user_model().objects.create_superuser(
            "test", "test@test.test", password
        )
        self.client.login(username=self.user.username, password=password)

    def test_redirect_when_one_result_after_searching(self):
        model = Foo
        obj = model.objects.create(bar="test1")
        info = model._meta.app_label, model._meta.model_name
        url = reverse("admin:{}_{}_changelist".format(*info))
        url += "?bar={}".format(obj.bar)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.endswith(obj.get_absolute_url()))

    def test_do_not_redirect_when_is_not_filtering(self):
        model = Foo
        model.objects.create(bar="test#1")
        info = model._meta.app_label, model._meta.model_name
        url = reverse("admin:{}_{}_changelist".format(*info))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
