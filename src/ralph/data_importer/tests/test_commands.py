import ipaddress
import os

from ddt import data, ddt, unpack
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core import management
from django.test import TestCase

from ralph.accounts.models import Region
from ralph.assets.models import ConfigurationClass
from ralph.assets.models.assets import (
    AssetModel,
    Category,
    Environment,
    Manufacturer,
    Service,
    ServiceEnvironment
)
from ralph.assets.models.choices import ObjectModelType
from ralph.back_office.models import BackOfficeAsset, Warehouse
from ralph.data_center.models import DataCenterAsset, DataCenterAssetStatus
from ralph.data_center.models.physical import DataCenter, Rack, ServerRoom
from ralph.data_center.tests.factories import DataCenterFactory
from ralph.data_importer.management.commands import importer
from ralph.data_importer.management.commands.create_server_model import (
    DEFAULT_MODEL_CATEGORY,
    DEFAULT_MODEL_MANUFACTURER,
    DEFAULT_MODEL_NAME
)
from ralph.data_importer.models import ImportedObjects
from ralph.data_importer.resources import AssetModelResource
from ralph.deployment.models import (
    Preboot,
    PrebootConfiguration,
    PrebootItemType
)
from ralph.dhcp.models import DNSServerGroup
from ralph.lib.transitions.conf import DEFAULT_ASYNC_TRANSITION_SERVICE_NAME
from ralph.lib.transitions.models import Transition, TransitionModel
from ralph.networks.models import IPAddress, Network


class DataImporterTestCase(TestCase):
    """TestCase data importer command."""

    def setUp(self):  # noqa
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        asset_model = AssetModel()
        asset_model.name = "asset_model_1"
        asset_model.type = ObjectModelType.back_office
        asset_model.save()
        asset_content_type = ContentType.objects.get_for_model(AssetModel)
        ImportedObjects.objects.create(
            content_type=asset_content_type, object_pk=asset_model.pk, old_object_pk=1
        )

        warehouse = Warehouse()
        warehouse.name = "warehouse_1"
        warehouse.save()

        warehouse_content_type = ContentType.objects.get_for_model(Warehouse)
        ImportedObjects.objects.create(
            content_type=warehouse_content_type, object_pk=warehouse.pk, old_object_pk=1
        )

        environment = Environment()
        environment.name = "environment_1"
        environment.save()

        service = Service()
        service.name = "service_1"
        service.save()

        service_environment = ServiceEnvironment()
        service_environment.environment = environment
        service_environment.service = service
        service_environment.save()

        region = Region(name="region_1")
        region.save()
        region_content_type = ContentType.objects.get_for_model(region)
        ImportedObjects.objects.create(
            content_type=region_content_type, object_pk=region.pk, old_object_pk=1
        )

        user_model = get_user_model()
        for user in ("iron.man", "superman", "james.bond", "sherlock.holmes"):
            user_model.objects.create(username=user)

    def test_get_resource(self):
        """Test get resources method."""
        asset_model_resource = importer.get_resource("AssetModel")
        self.assertIsInstance(asset_model_resource, AssetModelResource)

    def test_importer_command_warehouse(self):
        """Test importer management command with Warehouse model."""
        warehouse_csv = os.path.join(self.base_dir, "tests/samples/warehouses.csv")
        management.call_command(
            "importer",
            warehouse_csv,
            type="file",
            model_name="Warehouse",
            map_imported_id_to_new_id=True,
        )
        self.assertTrue(Warehouse.objects.filter(name="Poznań").exists())

    def test_importer_command_back_office_asset(self):
        """Test importer management command with BackOfficeAsset model."""
        back_office_csv = os.path.join(
            self.base_dir, "tests/samples/back_office_assets.csv"
        )
        management.call_command(
            "importer",
            back_office_csv,
            type="file",
            model_name="BackOfficeAsset",
            map_imported_id_to_new_id=True,
        )
        self.assertTrue(BackOfficeAsset.objects.filter(sn="bo_asset_sn").exists())
        back_office_asset = BackOfficeAsset.objects.get(sn="bo_asset_sn")
        self.assertEqual(back_office_asset.warehouse.name, "warehouse_1")
        self.assertEqual(back_office_asset.model.name, "asset_model_1")
        self.assertEqual(back_office_asset.service_env.service.name, "service_1")

    def test_importer_command_regions(self):
        """Test importer management command with BackOfficeAsset model."""
        old_regions_count = Region.objects.count()
        regions_csv = os.path.join(self.base_dir, "tests/samples/regions.csv")
        management.call_command(
            "importer",
            regions_csv,
            type="file",
            model_name="Region",
            map_imported_id_to_new_id=True,
        )
        self.assertEqual(Region.objects.count(), old_regions_count + 2)
        region_1 = Region.objects.get(name="USA")
        for user in ("iron.man", "superman"):
            self.assertIn(user, region_1.users.values_list("username", flat=True))

    def test_importer_command_with_tab(self):
        """Test importer management command with Warehouse model and
        tab separation file
        """
        warehouse_csv = os.path.join(self.base_dir, "tests/samples/warehouses_tab.csv")
        management.call_command(
            "importer",
            warehouse_csv,
            type="file",
            model_name="Warehouse",
            delimiter="\t",
            map_imported_id_to_new_id=True,
        )
        self.assertTrue(Warehouse.objects.filter(name="Barcelona").exists())

    def test_importer_command_with_skipid(self):
        """Test importer management command with Warehouse model and
        tab separation file
        """
        warehouse_csv = os.path.join(
            self.base_dir, "tests/samples/warehouses_skipid.csv"
        )
        management.call_command(
            "importer",
            warehouse_csv,
            "--skipid",
            type="file",
            model_name="Warehouse",
            delimiter=",",
            map_imported_id_to_new_id=True,
        )
        warehouse = Warehouse.objects.filter(name="Cupertino").first()
        self.assertNotEqual(warehouse.pk, 200)

        warehouse_content_type = ContentType.objects.get_for_model(Warehouse)
        warehouse_exists = ImportedObjects.objects.filter(
            content_type=warehouse_content_type, old_object_pk=200
        ).exists()
        self.assertTrue(warehouse_exists)

    def test_importer_command_with_semicolon(self):
        """Test importer management command with Warehouse model and
        semicolon separation file
        """
        warehouse_csv = os.path.join(
            self.base_dir, "tests/samples/warehouses_semicolon.csv"
        )
        management.call_command(
            "importer",
            warehouse_csv,
            type="file",
            model_name="Warehouse",
            delimiter=";",
            map_imported_id_to_new_id=True,
        )
        self.assertTrue(Warehouse.objects.filter(name="Berlin").exists())

    def test_imported_object(self):
        """Test importer management command with ImportedObjects model."""
        data_center = DataCenterFactory(name="CSV_test")
        data_center_content_type = ContentType.objects.get_for_model(DataCenter)
        ImportedObjects.objects.create(
            content_type=data_center_content_type,
            object_pk=data_center.pk,
            old_object_pk=1,
        )
        server_room_csv = os.path.join(self.base_dir, "tests/samples/server_room.csv")
        rack_csv = os.path.join(self.base_dir, "tests/samples/rack.csv")
        management.call_command(
            "importer",
            server_room_csv,
            type="file",
            model_name="ServerRoom",
            delimiter=",",
            map_imported_id_to_new_id=True,
        )

        content_type = ContentType.objects.get_for_model(ServerRoom)
        imported_object_exists = ImportedObjects.objects.filter(
            content_type=content_type, old_object_pk=1
        ).exists()
        self.assertTrue(imported_object_exists)

        management.call_command(
            "importer",
            rack_csv,
            type="file",
            model_name="Rack",
            delimiter=",",
            map_imported_id_to_new_id=True,
        )
        self.assertTrue(Rack.objects.filter(name="Rack_csv_test").exists())

    def test_from_dir_command(self):
        warehouse_dir = os.path.join(self.base_dir, "tests/samples/warehouses")
        management.call_command(
            "importer", warehouse_dir, type="dir", map_imported_id_to_new_id=True
        )

        self.assertTrue(Warehouse.objects.filter(name="From dir Warszawa").exists())
        self.assertTrue(Warehouse.objects.filter(name="From dir London").exists())

    def test_from_zipfile_command(self):
        warehouse_zip = os.path.join(self.base_dir, "tests/samples/warehouses.zip")
        management.call_command(
            "importer", warehouse_zip, type="zip", map_imported_id_to_new_id=True
        )

        self.assertTrue(Warehouse.objects.filter(name="From zip Warszawa").exists())

        self.assertTrue(Warehouse.objects.filter(name="From zip London").exists())


class IPManagementTestCase(TestCase):
    def setUp(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        asset_model = AssetModel()
        asset_model.id = 1  # required by csvs file
        asset_model.name = "asset_model_1"
        asset_model.type = ObjectModelType.all
        asset_model.save()

    def test_data_center_asset_is_imported_when_ip_management_is_created(self):
        xlsx_path = os.path.join(
            self.base_dir, "tests/samples/management_ip_existing.csv"
        )
        self.assertFalse(IPAddress.objects.filter(address="10.0.0.103").exists())

        management.call_command(
            "importer",
            xlsx_path,
            type="file",
            model_name="DataCenterAsset",
            map_imported_id_to_new_id=False,
        )

        self.assertTrue(DataCenterAsset.objects.get(hostname="EMC1-3"))
        self.assertTrue(
            DataCenterAsset.objects.get().ethernet_set.get().ipaddress.address,
            "10.0.0.103",
        )

    def test_data_center_asset_is_imported_when_ip_management_is_reused(self):
        IPAddress.objects.create(address="10.0.0.103")
        self.assertTrue(IPAddress.objects.filter(address="10.0.0.103").exists())

        xlsx_path = os.path.join(
            self.base_dir, "tests/samples/management_ip_existing.csv"
        )
        management.call_command(
            "importer",
            xlsx_path,
            type="file",
            model_name="DataCenterAsset",
            map_imported_id_to_new_id=False,
        )

        self.assertTrue(DataCenterAsset.objects.get(hostname="EMC1-3"))
        self.assertTrue(
            DataCenterAsset.objects.get().ethernet_set.get().ipaddress.address,
            "10.0.0.103",
        )

    def test_data_center_asset_is_imported_when_ip_management_is_blank(self):
        xlsx_path = os.path.join(self.base_dir, "tests/samples/management_ip_blank.csv")
        management.call_command(
            "importer",
            xlsx_path,
            type="file",
            model_name="DataCenterAsset",
            map_imported_id_to_new_id=False,
        )

        self.assertTrue(DataCenterAsset.objects.get(hostname="EMC1-3"))


@ddt
class TestCreateTransitionsCommand(TestCase):
    @classmethod
    def setUpTestData(cls):
        management.call_command("create_transitions")

    def test_transitions_generated(self):
        transitions = Transition.objects.all()
        self.assertEqual(3, transitions.count())

    @unpack
    @data(
        (
            "Deploy",
            [
                DataCenterAssetStatus.new.id,
                DataCenterAssetStatus.used.id,
                DataCenterAssetStatus.free.id,
                DataCenterAssetStatus.damaged.id,
                DataCenterAssetStatus.liquidated.id,
                DataCenterAssetStatus.to_deploy.id,
            ],
            [
                "assign_configuration_path",
                "assign_new_hostname",
                "assign_service_env",
                "clean_dhcp",
                "clean_hostname",
                "clean_ipaddresses",
                "cleanup_security_scans",
                "create_dhcp_entries",
                "create_dns_entries",
                "deploy",
                "wait_for_dhcp_servers",
                "wait_for_ping",
            ],
            DEFAULT_ASYNC_TRANSITION_SERVICE_NAME,
            0,
        ),
        (
            "Change config path",
            [
                DataCenterAssetStatus.new.id,
                DataCenterAssetStatus.used.id,
                DataCenterAssetStatus.free.id,
                DataCenterAssetStatus.damaged.id,
                DataCenterAssetStatus.liquidated.id,
                DataCenterAssetStatus.to_deploy.id,
            ],
            ["assign_configuration_path"],
            None,
            0,
        ),
        (
            "Reinstall",
            [
                DataCenterAssetStatus.new.id,
                DataCenterAssetStatus.used.id,
                DataCenterAssetStatus.free.id,
                DataCenterAssetStatus.damaged.id,
                DataCenterAssetStatus.liquidated.id,
                DataCenterAssetStatus.to_deploy.id,
            ],
            ["deploy", "wait_for_ping"],
            DEFAULT_ASYNC_TRANSITION_SERVICE_NAME,
            0,
        ),
    )
    def test_transition_of_each_type_generated(
        self, name, source, actions, async_service_name, target
    ):
        content_type = ContentType.objects.get_for_model(DataCenterAsset)

        try:
            transition = Transition.objects.get(
                model=TransitionModel.objects.get(content_type=content_type),
                name=name,
                source=source,
                async_service_name=async_service_name,
                target=target,
            )
        except Transition.DoesNotExist as e:
            self.fail(e)

        self.assertCountEqual(
            actions, [action.name for action in transition.actions.all()]
        )


class TestCreateNetworkCommand(TestCase):
    @classmethod
    def setUpTestData(cls):
        management.call_command("create_network", create_rack=True)

    def test_network_generated(self):
        networks = Network.objects.all()
        self.assertEqual(1, networks.count())

    def test_network_addressing_generated(self):
        try:
            network = Network.objects.get(name="10.0.0.0/24")
        except Network.DoesNotExist:
            self.fail("Expected network not created.")

        expected_gateway = "10.0.0.1"
        expected_dns = ["10.0.0.11", "10.0.0.12"]
        expected_dc = "dc1"

        self.assertEqual(ipaddress.ip_network("10.0.0.0/24"), network.address)
        self.assertEqual(expected_gateway, str(network.gateway))
        self.assertEqual(expected_dc, network.data_center.name)
        self.assertCountEqual(
            expected_dns,
            [
                str(server.ip_address)
                for server in network.dns_servers_group.servers.all()
            ],
        )

    def test_dns_group_generated(self):
        self.assertEqual(1, DNSServerGroup.objects.count())

    def test_dc_generated(self):
        self.assertEqual(1, DataCenter.objects.count())

    def test_racks_created(self):
        racks = Rack.objects.all()
        rack = racks[0]
        self.assertEqual(1, racks.count())
        self.assertTrue(rack.name.find("10.0.0.0/24"))
        self.assertEqual("server room", rack.server_room.name)


class TestCreateServerModelCommand(TestCase):
    @classmethod
    def setUpTestData(cls):
        management.call_command("create_server_model", model_is_blade_server=True)

    def test_server_model_generated(self):
        models = AssetModel.objects.all()
        model = models[0]
        self.assertEqual(1, models.count())
        self.assertEqual(1, Category.objects.count())
        self.assertEqual(1, Manufacturer.objects.count())
        self.assertEqual(DEFAULT_MODEL_NAME, model.name)
        self.assertEqual(DEFAULT_MODEL_CATEGORY, model.category.name)
        self.assertEqual(DEFAULT_MODEL_MANUFACTURER, model.manufacturer.name)


@ddt
class TestCreatePrebootCommand(TestCase):
    @classmethod
    def setUpTestData(cls):
        base_dir = os.path.dirname(os.path.dirname(__file__))
        samples_dir = os.path.join(base_dir, "tests", "samples")
        management.call_command(
            "create_preboot_configuration",
            kickstart_file=os.path.join(samples_dir, "kickstart_file"),
            ipxe_file=os.path.join(samples_dir, "ipxe_file"),
        )

    def test_preboot_details(self):
        preboot = Preboot.objects.first()
        kickstart = PrebootConfiguration.objects.filter(
            type=PrebootItemType.kickstart.id
        ).first()
        ipxe = PrebootConfiguration.objects.filter(type=PrebootItemType.ipxe.id).first()
        self.assertIn(kickstart, preboot.items.all())
        self.assertIn(ipxe, preboot.items.all())
        self.assertEqual("Preboot", preboot.name)
        self.assertEqual("Automatically generated preboot.", preboot.description)

    @unpack
    @data(
        (PrebootItemType.kickstart.id, "lang en_US\n"),
        (PrebootItemType.ipxe.id, "#!ipxe\n"),
    )
    def test_preboot_items_configuration(self, item_type, item_configuration):
        item = PrebootConfiguration.objects.filter(type=item_type).first()
        self.assertIn(item_configuration, item.configuration)

    @unpack
    @data(
        (PrebootItemType.kickstart.id, "Preboot kickstart"),
        (PrebootItemType.ipxe.id, "Preboot ipxe"),
    )
    def test_preboot_items_names(self, item_type, item_name):
        item = PrebootConfiguration.objects.filter(type=item_type).first()
        self.assertEqual(item_name, item.name)


@ddt
class TestInitialDataCommand(TestCase):
    @classmethod
    def setUpTestData(cls):
        management.call_command("initial_data")

    def test_networks_generated(self):
        networks = Network.objects.all()
        self.assertEqual(4, networks.count())

    @unpack
    @data(
        ("10.0.0.0/16", "10.0.0.1", "10.0.0.11", "10.0.0.12"),
        ("10.0.0.0/24", "10.0.0.1", "10.0.0.11", "10.0.0.12"),
        ("10.0.1.0/24", "10.0.1.1", "10.0.0.11", "10.0.0.12"),
        ("10.0.2.0/24", "10.0.2.1", "10.0.0.11", "10.0.0.12"),
    )
    def test_subnets_generated(
        self, network_address, gateway_address, dns1_address, dns2_address
    ):
        try:
            network = Network.objects.get(name=network_address)
        except Network.DoesNotExist:
            self.fail("Expected subnet {} not created.".format(network_address))

        expected_dns = [dns1_address, dns2_address]

        self.assertEqual(ipaddress.ip_network(network_address), network.address)
        self.assertEqual(gateway_address, str(network.gateway))
        self.assertCountEqual(
            expected_dns,
            [
                str(server.ip_address)
                for server in network.dns_servers_group.servers.all()
            ],
        )

    def test_user_created(self):
        try:
            user_model = get_user_model()
            user_model.objects.get(username="admin")
        except user_model.DoesNotExist:
            self.fail("Admin user not created.")

    def test_configuration_path_created(self):
        try:
            ConfigurationClass.objects.get(path="configuration_module/default")
        except ConfigurationClass.DoesNotExist:
            self.fail("Default configuration path not created.")

    def test_asset_models_created(self):
        self.assertEqual(6, AssetModel.objects.count())
        for name in ["A", "B", "C"]:
            try:
                AssetModel.objects.get(name="Model {}".format(name))
            except AssetModel.DoesNotExist:
                self.fail(
                    'Asset model with name "Model {}" does not exist.'.format(name)
                )
        for name in ["A", "B", "C"]:
            try:
                AssetModel.objects.get(name="Blade server model {}".format(name))
            except AssetModel.DoesNotExist:
                self.fail(
                    'Asset model with name "Blade server model {}" does not exist.'.format(
                        name
                    )
                )
