# -*- coding: utf-8 -*-
from ddt import data, ddt, unpack
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models import Field

from ralph.accounts.tests.factories import RegionFactory
from ralph.back_office.models import BackOfficeAsset, BackOfficeAssetStatus
from ralph.back_office.tests.factories import WarehouseFactory
from ralph.data_center.models.choices import DataCenterAssetStatus, Orientation
from ralph.data_center.models.physical import (
    assign_additional_hostname_choices,
    DataCenterAsset
)
from ralph.data_center.models.virtual import BaseObjectCluster
from ralph.data_center.tests.factories import (
    ClusterFactory,
    ClusterTypeFactory,
    DataCenterAssetFactory,
    DataCenterAssetModelFactory,
    RackFactory
)
from ralph.lib.transitions.models import Transition, TransitionModel
from ralph.networks.models import IPAddress
from ralph.networks.tests.factories import (
    IPAddressFactory,
    NetworkEnvironmentFactory,
    NetworkFactory
)
from ralph.tests import RalphTestCase


@ddt
class DataCenterAssetTest(RalphTestCase):
    def setUp(self):
        self.dc_asset = DataCenterAssetFactory(
            status=DataCenterAssetStatus.liquidated.id
        )
        self.dc_asset_2 = DataCenterAssetFactory(
            parent=self.dc_asset,
        )
        self.dc_asset_3 = DataCenterAssetFactory()

    def test_convert_to_backoffice_asset(self):
        dc_asset = DataCenterAssetFactory()
        transition = Transition.objects.create(
            name="transition",
            model=TransitionModel.get_for_field(dc_asset, "status"),
            source=0,
            target=0,
        )
        dc_asset_pk = dc_asset.pk
        hostname = dc_asset.hostname
        DataCenterAsset.convert_to_backoffice_asset(
            instances=[dc_asset],
            region=RegionFactory().id,
            warehouse=WarehouseFactory().id,
            request=None,
            transition_id=transition.pk,
        )
        bo_asset = BackOfficeAsset.objects.get(pk=dc_asset_pk)
        self.assertFalse(DataCenterAsset.objects.filter(pk=dc_asset_pk).exists())
        self.assertEqual(bo_asset.hostname, hostname)

    def test_convert_to_backoffice_asset_preserves_status_name(self):
        dc_asset = DataCenterAssetFactory(
            status=DataCenterAssetStatus.from_name("damaged")
        )
        transition = Transition.objects.create(
            name="transition",
            model=TransitionModel.get_for_field(dc_asset, "status"),
            source=0,
            target=0,
        )
        dc_asset_pk = dc_asset.pk
        dc_asset_status_name = DataCenterAssetStatus.from_id(dc_asset.status).name
        DataCenterAsset.convert_to_backoffice_asset(
            instances=[dc_asset],
            region=RegionFactory().id,
            warehouse=WarehouseFactory().id,
            request=None,
            transition_id=transition.pk,
        )
        bo_asset = BackOfficeAsset.objects.get(pk=dc_asset_pk)
        bo_asset_status_name = BackOfficeAssetStatus.from_id(bo_asset.status).name
        self.assertEqual(dc_asset_status_name, bo_asset_status_name)

    def test_convert_to_backoffice_asset_uses_default_from_transition(self):
        target_status_id = BackOfficeAssetStatus.from_name(
            "new"  # status name common for dc_asset and bo_asset
        ).id
        dc_asset = DataCenterAssetFactory(
            status=DataCenterAssetStatus.from_name("damaged")
        )
        transition = Transition.objects.create(
            name="transition",
            model=TransitionModel.get_for_field(dc_asset, "status"),
            source=0,
            target=target_status_id,
        )
        dc_asset_pk = dc_asset.pk
        target_status_name = DataCenterAssetStatus.from_id(target_status_id).name
        DataCenterAsset.convert_to_backoffice_asset(
            instances=[dc_asset],
            region=RegionFactory().id,
            warehouse=WarehouseFactory().id,
            request=None,
            transition_id=transition.pk,
        )
        bo_asset = BackOfficeAsset.objects.get(pk=dc_asset_pk)
        bo_asset_status_name = BackOfficeAssetStatus.from_id(bo_asset.status).name
        self.assertEqual(target_status_name, bo_asset_status_name)

    def test_convert_to_backoffice_asset_uses_default_from_settings(self):
        target_status_id = BackOfficeAssetStatus.from_id(
            settings.CONVERT_TO_BACKOFFICE_ASSET_DEFAULT_STATUS_ID
        ).id
        dc_asset = DataCenterAssetFactory(
            status=DataCenterAssetStatus.from_name("pre_liquidated")
        )
        transition = Transition.objects.create(
            name="transition",
            model=TransitionModel.get_for_field(dc_asset, "status"),
            source=0,
            target=0,
        )
        dc_asset_pk = dc_asset.pk
        target_status_name = DataCenterAssetStatus.from_id(target_status_id).name
        DataCenterAsset.convert_to_backoffice_asset(
            instances=[dc_asset],
            region=RegionFactory().id,
            warehouse=WarehouseFactory().id,
            request=None,
            transition_id=transition.pk,
        )
        bo_asset = BackOfficeAsset.objects.get(pk=dc_asset_pk)
        bo_asset_status_name = BackOfficeAssetStatus.from_id(bo_asset.status).name
        self.assertEqual(target_status_name, bo_asset_status_name)

    # =========================================================================
    # slot_no
    #  =========================================================================
    @unpack
    @data(
        ("1A",),
        ("1B",),
        ("9A",),
        ("9B",),
        ("10A",),
        ("10B",),
        ("16A",),
        ("16B",),
        ("1",),
        ("9",),
        ("10",),
        ("16",),
    )
    def test_should_pass_when_slot_no_is_correct(self, slot_no):
        slot_no_field: Field = self.dc_asset._meta.get_field("slot_no")
        slot_no_field.clean(slot_no, self.dc_asset)

    @unpack
    @data(
        ("1C",),
        ("0A",),
        ("0",),
        ("B",),
        ("17A",),
        ("17B",),
        ("20A",),
        ("1a",),
        ("1b",),
        ("111",),
    )
    def test_should_raise_validation_error_when_slot_no_is_incorrect(self, slot_no):
        slot_no_field: Field = self.dc_asset._meta.get_field("slot_no")
        with self.assertRaises(ValidationError):
            slot_no_field.clean(slot_no, self.dc_asset)

    def test_should_raise_validation_error_when_slot_no_is_busy(self):
        model = DataCenterAssetModelFactory(has_parent=True)
        DataCenterAssetFactory(parent=self.dc_asset, slot_no=1, model=model)
        dc_asset = DataCenterAssetFactory(parent=self.dc_asset, model=model)
        dc_asset.slot_no = 1
        with self.assertRaises(ValidationError):
            dc_asset.clean()

    def test_should_pass_when_slot_no_is_busy_but_different_orientation(self):
        model = DataCenterAssetModelFactory(has_parent=True)
        DataCenterAssetFactory(
            parent=self.dc_asset,
            slot_no=1,
            model=model,
            orientation=Orientation.back,
        )
        dc_asset = DataCenterAssetFactory(parent=self.dc_asset, model=model)
        dc_asset.slot_no = 1
        dc_asset._validate_slot_no()

    def test_should_raise_validation_error_when_empty_slot_no_on_blade(self):
        dc_asset = DataCenterAssetFactory(model__has_parent=True)
        dc_asset.slot_no = ""
        with self.assertRaises(ValidationError):
            dc_asset._validate_slot_no()

    def test_should_raise_validation_error_when_slot_not_filled_when_not_blade(self):  # noqa
        dc_asset = DataCenterAssetFactory(model__has_parent=False)
        dc_asset.slot_no = "1A"
        with self.assertRaises(ValidationError):
            dc_asset._validate_slot_no()

    def test_should_pass_when_slot_no_filled_on_blade(self):
        dc_asset = DataCenterAssetFactory(model__has_parent=True)
        dc_asset.slot_no = "1A"
        dc_asset._validate_slot_no()

    def test_should_pass_when_slot_not_filled_without_model(self):
        dc_asset = DataCenterAsset()
        dc_asset.slot_no = "1A"
        dc_asset._validate_slot_no()

    # =========================================================================
    # orientation
    # =========================================================================
    @unpack
    @data(
        (None, Orientation.front),
        (None, Orientation.left),
        (0, Orientation.left),
        (0, Orientation.right),
        (1, Orientation.front),
        (10, Orientation.back),
        (100, Orientation.middle),
    )
    def test_should_pass_when_orientation_is_correct(self, position, orientation):
        self.dc_asset.position = position
        self.dc_asset.orientation = orientation
        self.dc_asset._validate_orientation()

    @unpack
    @data(
        (0, Orientation.front),
        (0, Orientation.back),
        (0, Orientation.middle),
        (1, Orientation.left),
        (10, Orientation.right),
    )
    def test_should_raise_validation_error_when_orientation_is_correct(
        self, position, orientation
    ):
        self.dc_asset.position = position
        self.dc_asset.orientation = orientation
        with self.assertRaises(ValidationError):
            self.dc_asset._validate_orientation()

    # =========================================================================
    # position in rack
    # =========================================================================
    @unpack
    @data(
        (None, 100),
        (10, 10),
        (10, 100),
    )
    def test_should_pass_when_position_in_rack_is_correct(
        self, position, rack_max_height
    ):
        self.dc_asset.position = position
        self.dc_asset.rack = RackFactory(max_u_height=rack_max_height)
        self.dc_asset._validate_position_in_rack()

    def test_should_pass_when_rack_is_null(self):
        self.dc_asset.position = 10
        self.dc_asset.rack = None
        self.dc_asset._validate_position_in_rack()

    @unpack
    @data((10, 9), (1, 0), (-1, 10))
    def test_should_raise_validation_error_when_position_in_rack_is_incorrect(
        self, position, rack_max_height
    ):
        self.dc_asset.position = position
        self.dc_asset.rack = RackFactory(max_u_height=rack_max_height)
        with self.assertRaises(ValidationError):
            self.dc_asset._validate_position_in_rack()

    # =========================================================================
    # position requirement
    # =========================================================================
    def test_should_pass_when_position_is_passed_and_rack_requires_it(self):
        self.dc_asset.position = 10
        self.dc_asset.rack = RackFactory(require_position=True)
        self.dc_asset._validate_position()

    def test_should_pass_when_position_is_passed_and_rack_doesnt_require_it(self):  # noqa
        self.dc_asset.position = 10
        self.dc_asset.rack = RackFactory(require_position=False)
        self.dc_asset._validate_position()

    def test_should_pass_when_position_is_not_passed_and_rack_doesnt_require_it(self):  # noqa
        self.dc_asset.position = None
        self.dc_asset.rack = RackFactory(require_position=False)
        self.dc_asset._validate_position()

    def test_should_raise_validation_error_when_position_is_not_passed_and_rack_requires_it(
        self,
    ):  # noqa
        self.dc_asset.position = None
        self.dc_asset.rack = RackFactory(require_position=True)
        with self.assertRaises(ValidationError):
            self.dc_asset._validate_position()

    def test_update_rack_when_parent_rack_is_change(self):
        rack_1, rack_2 = RackFactory.create_batch(2)
        parent_asset = DataCenterAssetFactory(
            rack=rack_1, model=DataCenterAssetModelFactory(has_parent=True)
        )
        dc_asset = DataCenterAssetFactory(parent=parent_asset)
        parent_asset.rack = rack_2
        parent_asset.save()
        dc_asset.refresh_from_db()
        self.assertEqual(dc_asset.rack_id, rack_2.id)

    def test_update_position_when_parent_position_is_change(self):
        rack = RackFactory()
        parent_asset = DataCenterAssetFactory(
            rack=rack, position=1, model=DataCenterAssetModelFactory(has_parent=True)
        )
        dc_asset = DataCenterAssetFactory(parent=parent_asset, position=2)
        parent_asset.position = 4
        parent_asset.save()
        dc_asset.refresh_from_db()
        self.assertEqual(dc_asset.position, 4)

    # =========================================================================
    # network environment
    # =========================================================================
    def _prepare_rack(self, dc_asset, address, network_address, rack=None):
        self.rack = rack or RackFactory()
        self.net_env = NetworkEnvironmentFactory(
            hostname_template_prefix="server_1",
            hostname_template_postfix=".mydc.net",
        )
        self.net_env2 = NetworkEnvironmentFactory(
            hostname_template_prefix="server_2",
            hostname_template_postfix=".mydc.net",
        )
        self.net = NetworkFactory(
            network_environment=self.net_env,
            address=network_address,
        )
        self.net2 = NetworkFactory(
            network_environment=self.net_env2,
            address="10.20.30.0/24",
        )
        self.net.racks.add(self.rack)
        self.net2.racks.add(self.rack)
        dc_asset.rack = self.rack
        dc_asset.save()
        IPAddressFactory(ethernet__base_object=self.dc_asset, address=address)

    def test_network_environment(self):
        self._prepare_rack(self.dc_asset, "192.168.1.11", "192.168.1.0/24")

        self.assertEqual(self.dc_asset.network_environment, self.net_env)

    def test_network_environment_null(self):
        self._prepare_rack(self.dc_asset, "192.168.1.11", "192.222.1.0/24")
        self.assertIsNone(self.dc_asset.network_environment)

    # =========================================================================
    # next free hostname
    # =========================================================================
    def test_get_next_free_hostname(self):
        self._prepare_rack(self.dc_asset, "192.168.1.11", "192.168.1.0/24")
        self.assertEqual(
            self.dc_asset.get_next_free_hostname(), "server_10001.mydc.net"
        )
        # running it again shouldn't change next hostname
        self.assertEqual(
            self.dc_asset.get_next_free_hostname(), "server_10001.mydc.net"
        )

    def test_get_next_free_hostname_without_network_env(self):
        self.assertEqual(self.dc_asset.get_next_free_hostname(), "")

    def test_issue_next_free_hostname(self):
        self._prepare_rack(self.dc_asset, "192.168.1.11", "192.168.1.0/24")
        self.assertEqual(
            self.dc_asset.issue_next_free_hostname(), "server_10001.mydc.net"
        )
        # running it again should change next hostname
        self.assertEqual(
            self.dc_asset.issue_next_free_hostname(), "server_10002.mydc.net"
        )

    def test_issue_next_free_hostname_without_network_env(self):
        self.assertEqual(self.dc_asset.issue_next_free_hostname(), "")

    # =========================================================================
    # available networks
    # =========================================================================
    def test_get_available_networks(self):
        self._prepare_rack(self.dc_asset, "192.168.1.1", "192.168.1.0/24")
        self.net3 = NetworkFactory(address="192.168.3.0/24")

        self.assertCountEqual(
            self.dc_asset._get_available_networks(), [self.net, self.net2]
        )

    def test_get_available_networks_is_broadcasted_in_dhcp(self):
        self._prepare_rack(self.dc_asset, "192.168.1.1", "192.168.1.0/24")
        self.net3 = NetworkFactory(address="192.168.3.0/24", dhcp_broadcast=True)
        self.assertCountEqual(
            self.dc_asset._get_available_networks(is_broadcasted_in_dhcp=True),
            [self.net, self.net2],
        )

    def test_get_available_networks_no_rack(self):
        NetworkFactory(address="192.168.1.0/24")
        NetworkFactory(address="192.168.2.0/24")
        self.assertEqual(self.dc_asset._get_available_networks(), [])

    # =========================================================================
    # other
    # =========================================================================
    def test_change_rack_in_descendants(self):
        self.dc_asset.rack = RackFactory()
        self.dc_asset.save()
        asset = DataCenterAsset.objects.get(pk=self.dc_asset_2.pk)

        self.assertEqual(self.dc_asset.rack_id, asset.rack_id)

    def test_get_autocomplete_queryset(self):
        queryset = DataCenterAsset.get_autocomplete_queryset()
        self.assertEqual(2, queryset.count())

    # =========================================================================
    # management_ip
    # =========================================================================
    def test_assign_new_management_ip_should_pass(self):
        self.dc_asset.management_ip = "10.20.30.40"
        self.dc_asset.refresh_from_db()
        self.assertEqual(self.dc_asset.management_ip, "10.20.30.40")

    def test_assign_existing_ip_assigned_to_another_obj_should_not_pass(self):
        IPAddressFactory(address="10.20.30.40", is_management=True)
        with self.assertRaises(ValidationError):
            self.dc_asset.management_ip = "10.20.30.40"

    def test_assign_existing_ip_not_assigned_to_another_obj_should_pass(self):
        IPAddressFactory(address="10.20.30.40", ethernet=None)
        self.dc_asset.management_ip = "10.20.30.40"
        self.dc_asset.refresh_from_db()
        self.assertEqual(self.dc_asset.management_ip, "10.20.30.40")

    def test_change_mgmt_ip_for_new_ip_should_pass(self):
        self.dc_asset.management_ip = "10.20.30.40"
        self.dc_asset.refresh_from_db()
        self.assertEqual(self.dc_asset.management_ip, "10.20.30.40")
        self.dc_asset.management_ip = "10.20.30.41"
        self.dc_asset.refresh_from_db()
        self.assertEqual(self.dc_asset.management_ip, "10.20.30.41")
        self.assertFalse(IPAddress.objects.filter(address="10.20.30.40").exists())

    def test_change_mgmt_ip_for_existing_ip_without_object_should_pass(self):
        IPAddressFactory(address="10.20.30.42", ethernet=None)
        self.dc_asset.management_ip = "10.20.30.40"
        self.dc_asset.refresh_from_db()
        self.assertEqual(self.dc_asset.management_ip, "10.20.30.40")
        self.dc_asset.management_ip = "10.20.30.42"
        self.dc_asset.refresh_from_db()
        self.assertEqual(self.dc_asset.management_ip, "10.20.30.42")
        self.assertFalse(IPAddress.objects.filter(address="10.20.30.40").exists())

    def test_change_mgmt_ip_for_existing_ip_with_object_should_not_pass(self):
        IPAddressFactory(address="10.20.30.42")
        self.dc_asset.management_ip = "10.20.30.40"
        self.dc_asset.refresh_from_db()
        self.assertEqual(self.dc_asset.management_ip, "10.20.30.40")
        with self.assertRaises(ValidationError):
            self.dc_asset.management_ip = "10.20.30.42"

    def test_should_return_only_common_networks(self):
        rack100 = RackFactory()
        rack101 = RackFactory()
        rack_100_net = NetworkFactory(address="10.0.100.0/24")
        rack_101_net = NetworkFactory(address="10.0.101.0/24")
        common_net = NetworkFactory(address="10.0.0.0/24")
        rack_100_net.racks.set([rack100])
        rack_101_net.racks.set([rack101])
        common_net.racks.set([rack100, rack101])
        self.dc_asset_2.rack = rack100
        self.dc_asset_3.rack = rack101

        rack_100_result = assign_additional_hostname_choices(None, [self.dc_asset_2])
        common_result = assign_additional_hostname_choices(
            None, [self.dc_asset_2, self.dc_asset_3]
        )
        expected_rack100_result = [
            (str(rack_100_net.pk), rack_100_net),
            (str(common_net.pk), common_net),
        ]
        expected_common_result = [(str(common_net.pk), common_net)]
        self.assertCountEqual(rack_100_result, expected_rack100_result)
        self.assertEqual(len(rack_100_result), 2)
        self.assertCountEqual(common_result, expected_common_result)
        self.assertEqual(len(common_result), 1)


@ddt
class RackTest(RalphTestCase):
    def test_get_free_u_in_empty_rack_should_return_max_u_height(self):
        rack = RackFactory()
        self.assertEqual(rack.get_free_u(), rack.max_u_height)

    @unpack
    @data(
        (1, 47, 47, 0),
        (1, 46, 47, 1),
        (2, 45, 47, 2),
        (47, 1, 47, 46),
        (47, 5, 47, 46),
    )
    def test_get_free_u_for_one_asset(self, position, height, max_u_height, expected):
        rack = RackFactory(max_u_height=max_u_height)
        asset_kwargs = {
            "rack": rack,
            "model__height_of_device": height,
            "position": position,
            "slot_no": None,
            "orientation": Orientation.front.id,
        }
        DataCenterAssetFactory(**asset_kwargs)
        self.assertEqual(rack.get_free_u(), expected)

    def test_get_free_u_for_none_position(self):
        rack = RackFactory(max_u_height=47)
        asset_kwargs = {
            "rack": rack,
            "model__height_of_device": 47,
            "position": None,
            "slot_no": None,
            "orientation": Orientation.front.id,
        }
        DataCenterAssetFactory(**asset_kwargs)
        self.assertEqual(rack.get_free_u(), 47)

    def test_get_free_u_should_respect_orientation(self):
        rack = RackFactory(max_u_height=48)
        asset_common_kwargs = {
            "rack": rack,
            "model__height_of_device": 1,
            "position": 35,
            "slot_no": None,
        }
        DataCenterAssetFactory(orientation=Orientation.front.id, **asset_common_kwargs)
        DataCenterAssetFactory(orientation=Orientation.back.id, **asset_common_kwargs)
        self.assertEqual(rack.get_free_u(), 47)


class ClusterTest(RalphTestCase):
    def setUp(self):
        self.cluster_type = ClusterTypeFactory()
        self.cluster_1 = ClusterFactory()
        self.boc_1 = BaseObjectCluster.objects.create(
            cluster=self.cluster_1, base_object=DataCenterAssetFactory()
        )
        self.master = DataCenterAssetFactory()
        self.boc_2 = BaseObjectCluster.objects.create(
            cluster=self.cluster_1, base_object=self.master, is_master=True
        )

    def test_masters(self):
        self.assertEqual(self.cluster_1.masters, [self.master])


class TestDataCenterAssetStatuses(RalphTestCase):
    def test_status_ids_are_consistent(self):
        """
        Tests that adding choice keeps ids the same (choices should be
        appended)
        """
        statuses = DataCenterAssetStatus()
        self.assertEqual(
            statuses,
            [
                (1, "new"),
                (2, "in use"),
                (3, "free"),
                (4, "damaged"),
                (5, "liquidated"),
                (6, "to deploy"),
                (7, "cleaned"),
                (8, "pre liquidated"),
            ],
        )
