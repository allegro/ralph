# -*- coding: utf-8 -*-
from ddt import data, ddt, unpack
from django.core.exceptions import ValidationError

from ralph.accounts.tests.factories import RegionFactory
from ralph.back_office.models import BackOfficeAsset
from ralph.back_office.tests.factories import WarehouseFactory
from ralph.data_center.models.choices import DataCenterAssetStatus, Orientation
from ralph.data_center.models.physical import DataCenterAsset
from ralph.data_center.models.virtual import BaseObjectCluster
from ralph.data_center.tests.factories import (
    ClusterFactory,
    ClusterTypeFactory,
    DataCenterAssetFactory,
    RackFactory
)
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

    def test_convert_to_backoffice_asset(self):
        dc_asset = DataCenterAssetFactory()
        dc_asset_pk = dc_asset.pk
        hostname = dc_asset.hostname
        DataCenterAsset.convert_to_backoffice_asset(
            instances=[dc_asset],
            region=RegionFactory().id,
            warehouse=WarehouseFactory().id,
            request=None
        )
        bo_asset = BackOfficeAsset.objects.get(pk=dc_asset_pk)
        self.assertFalse(
            DataCenterAsset.objects.filter(pk=dc_asset_pk).exists()
        )
        self.assertEqual(bo_asset.hostname, hostname)

    # =========================================================================
    # slot_no
    #  =========================================================================
    @unpack
    @data(
        ('1A',),
        ('1B',),
        ('9A',),
        ('9B',),
        ('10A',),
        ('10B',),
        ('16A',),
        ('16B',),
        ('1',),
        ('9',),
        ('10',),
        ('16',),
    )
    def test_should_pass_when_slot_no_is_correct(self, slot_no):
        slot_no_field = self.dc_asset._meta.get_field_by_name('slot_no')[0]
        slot_no_field.clean(slot_no, self.dc_asset)

    @unpack
    @data(
        ('1C',),
        ('0A',),
        ('0',),
        ('B',),
        ('17A',),
        ('17B',),
        ('20A',),
        ('1a',),
        ('1b',),
        ('111',),
    )
    def test_should_raise_validation_error_when_slot_no_is_incorrect(
        self, slot_no
    ):
        slot_no_field = self.dc_asset._meta.get_field_by_name('slot_no')[0]
        with self.assertRaises(ValidationError):
            slot_no_field.clean(slot_no, self.dc_asset)

    def test_should_raise_validation_error_when_empty_slot_no_on_blade(self):
        dc_asset = DataCenterAssetFactory(model__has_parent=True)
        dc_asset.slot_no = ''
        with self.assertRaises(ValidationError):
            dc_asset._validate_slot_no()

    def test_should_raise_validation_error_when_slot_not_filled_when_not_blade(self):  # noqa
        dc_asset = DataCenterAssetFactory(model__has_parent=False)
        dc_asset.slot_no = '1A'
        with self.assertRaises(ValidationError):
            dc_asset._validate_slot_no()

    def test_should_pass_when_slot_no_filled_on_blade(self):
        dc_asset = DataCenterAssetFactory(model__has_parent=True)
        dc_asset.slot_no = '1A'
        dc_asset._validate_slot_no()

    def test_should_pass_when_slot_not_filled_without_model(self):
        dc_asset = DataCenterAsset()
        dc_asset.slot_no = '1A'
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
    def test_should_pass_when_orientation_is_correct(
        self, position, orientation
    ):
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
    @data(
        (10, 9),
        (1, 0),
        (-1, 10)
    )
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

    def test_should_raise_validation_error_when_position_is_not_passed_and_rack_requires_it(self):  # noqa
        self.dc_asset.position = None
        self.dc_asset.rack = RackFactory(require_position=True)
        with self.assertRaises(ValidationError):
            self.dc_asset._validate_position()

    # =========================================================================
    # network environment
    # =========================================================================
    def _prepare_rack(self, dc_asset, network_address, rack=None):
        self.rack = rack or RackFactory()
        self.net_env = NetworkEnvironmentFactory(
            hostname_template_prefix='server_1',
            hostname_template_postfix='.mydc.net',
        )
        self.net = NetworkFactory(
            network_environment=self.net_env,
            address=network_address,
        )
        self.net.racks.add(self.rack)
        dc_asset.rack = self.rack
        dc_asset.save()

    def test_network_environment(self):
        self._prepare_rack(self.dc_asset, '192.168.1.0/24')
        self.assertEqual(self.dc_asset.network_environment, self.net_env)

    # =========================================================================
    # next free hostname
    # =========================================================================
    def test_get_next_free_hostname(self):
        self._prepare_rack(self.dc_asset, '192.168.1.0/24')
        self.assertEqual(
            self.dc_asset.get_next_free_hostname(),
            'server_10001.mydc.net'
        )
        # running it again shouldn't change next hostname
        self.assertEqual(
            self.dc_asset.get_next_free_hostname(),
            'server_10001.mydc.net'
        )

    def test_get_next_free_hostname_without_network_env(self):
        self.assertEqual(self.dc_asset.get_next_free_hostname(), '')

    def test_issue_next_free_hostname(self):
        self._prepare_rack(self.dc_asset, '192.168.1.0/24')
        self.assertEqual(
            self.dc_asset.issue_next_free_hostname(),
            'server_10001.mydc.net'
        )
        # running it again should change next hostname
        self.assertEqual(
            self.dc_asset.issue_next_free_hostname(),
            'server_10002.mydc.net'
        )

    def test_issue_next_free_hostname_without_network_env(self):
        self.assertEqual(self.dc_asset.issue_next_free_hostname(), '')

    # =========================================================================
    # other
    # =========================================================================
    def test_change_rack_in_descendants(self):
        self.dc_asset.rack = RackFactory()
        self.dc_asset.save()
        asset = DataCenterAsset.objects.get(pk=self.dc_asset_2.pk)

        self.assertEquals(self.dc_asset.rack_id, asset.rack_id)

    def test_get_autocomplete_queryset(self):
        queryset = DataCenterAsset.get_autocomplete_queryset()
        self.assertEquals(1, queryset.count())

    # =========================================================================
    # management_ip
    # =========================================================================
    def test_assign_new_management_ip_should_pass(self):
        self.dc_asset.management_ip = '10.20.30.40'
        self.dc_asset.refresh_from_db()
        self.assertEqual(self.dc_asset.management_ip, '10.20.30.40')

    def test_assign_existing_ip_assigned_to_another_obj_should_not_pass(self):
        IPAddressFactory(address='10.20.30.40', is_management=True)
        with self.assertRaises(ValidationError):
            self.dc_asset.management_ip = '10.20.30.40'

    def test_assign_existing_ip_not_assigned_to_another_obj_should_pass(self):
        IPAddressFactory(address='10.20.30.40', ethernet=None)
        self.dc_asset.management_ip = '10.20.30.40'
        self.dc_asset.refresh_from_db()
        self.assertEqual(self.dc_asset.management_ip, '10.20.30.40')

    def test_change_mgmt_ip_for_new_ip_should_pass(self):
        self.dc_asset.management_ip = '10.20.30.40'
        self.dc_asset.refresh_from_db()
        self.assertEqual(self.dc_asset.management_ip, '10.20.30.40')
        self.dc_asset.management_ip = '10.20.30.41'
        self.dc_asset.refresh_from_db()
        self.assertEqual(self.dc_asset.management_ip, '10.20.30.41')
        self.assertFalse(
            IPAddress.objects.filter(address='10.20.30.40').exists()
        )

    def test_change_mgmt_ip_for_existing_ip_without_object_should_pass(self):
        IPAddressFactory(address='10.20.30.42', ethernet=None)
        self.dc_asset.management_ip = '10.20.30.40'
        self.dc_asset.refresh_from_db()
        self.assertEqual(self.dc_asset.management_ip, '10.20.30.40')
        self.dc_asset.management_ip = '10.20.30.42'
        self.dc_asset.refresh_from_db()
        self.assertEqual(self.dc_asset.management_ip, '10.20.30.42')
        self.assertFalse(
            IPAddress.objects.filter(address='10.20.30.40').exists()
        )

    def test_change_mgmt_ip_for_existing_ip_with_object_should_not_pass(self):
        IPAddressFactory(address='10.20.30.42')
        self.dc_asset.management_ip = '10.20.30.40'
        self.dc_asset.refresh_from_db()
        self.assertEqual(self.dc_asset.management_ip, '10.20.30.40')
        with self.assertRaises(ValidationError):
            self.dc_asset.management_ip = '10.20.30.42'


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
    def test_get_free_u_for_one_asset(
        self, position, height, max_u_height, expected
    ):
        rack = RackFactory(max_u_height=max_u_height)
        asset_kwargs = {
            'rack': rack,
            'model__height_of_device': height,
            'position': position,
            'slot_no': None,
            'orientation': Orientation.front.id,
        }
        DataCenterAssetFactory(**asset_kwargs)
        self.assertEqual(rack.get_free_u(), expected)

    def test_get_free_u_for_none_position(self):
        rack = RackFactory(max_u_height=47)
        asset_kwargs = {
            'rack': rack,
            'model__height_of_device': 47,
            'position': None,
            'slot_no': None,
            'orientation': Orientation.front.id,
        }
        DataCenterAssetFactory(**asset_kwargs)
        self.assertEqual(rack.get_free_u(), 47)

    def test_get_free_u_should_respect_orientation(self):
        rack = RackFactory(max_u_height=48)
        asset_common_kwargs = {
            'rack': rack,
            'model__height_of_device': 1,
            'position': 35,
            'slot_no': None
        }
        DataCenterAssetFactory(
            orientation=Orientation.front.id, **asset_common_kwargs
        )
        DataCenterAssetFactory(
            orientation=Orientation.back.id, **asset_common_kwargs
        )
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
            cluster=self.cluster_1, base_object=self.master,
            is_master=True
        )

    def test_masters(self):
        self.assertEqual(self.cluster_1.masters, [self.master])
