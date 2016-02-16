# -*- coding: utf-8 -*-
from ddt import data, ddt, unpack
from django.core.exceptions import ValidationError

from ralph.accounts.tests.factories import RegionFactory
from ralph.back_office.models import BackOfficeAsset
from ralph.back_office.tests.factories import WarehouseFactory
from ralph.data_center.models.choices import DataCenterAssetStatus, Orientation
from ralph.data_center.models.networks import (
    get_network_tree,
    IPAddress,
    Network
)
from ralph.data_center.models.physical import DataCenterAsset
from ralph.data_center.tests.factories import (
    DataCenterAssetFactory,
    RackFactory
)
from ralph.tests import RalphTestCase


class NetworkTest(RalphTestCase):
    def setUp(self):
        self.net1 = Network.objects.create(
            name="test1",
            address="192.168.0.0/16",
        )
        self.net2 = Network.objects.create(
            name="test2",
            address="192.168.0.0/17",
        )
        self.net3 = Network.objects.create(
            name="test3",
            address="192.168.128.0/17",
            reserved=5,
            reserved_top_margin=5,
        )
        self.net4 = Network.objects.create(
            name="test4",
            address="192.168.133.0/24",
        )
        self.net5 = Network.objects.create(
            name="test5",
            address="192.169.133.0/24",
        )

        self.ip1 = IPAddress(address="192.168.128.10")
        self.ip1.save()
        self.ip2 = IPAddress(address="192.168.133.10")
        self.ip2.save()
        self.ip3 = IPAddress(address="192.168.128.11")
        self.ip3.save()

    def test_get_netmask(self):
        self.assertEquals(self.net1.get_netmask(), 16)
        self.assertEquals(self.net2.get_netmask(), 17)

    def test_get_subnetworks(self):
        res = self.net1.get_subnetworks()
        correct = [self.net2, self.net3, self.net4]
        self.assertEquals(res, correct)

        res = self.net3.get_subnetworks()
        correct = [self.net4]
        self.assertEquals(res, correct)

    def test_get_address_summary(self):
        ret = self.net3.get_total_ips()
        self.assertEquals(ret, 32767)
        ret = self.net3.get_free_ips()
        self.assertEquals(ret, 32500)
        ret = self.net3.get_ip_usage_range()
        correct_range = [self.ip1, self.ip3, self.net4]
        self.assertEquals(ret, correct_range)

    def test_get_ip_usage_aggregated(self):
        ret = self.net3.get_ip_usage_aggregated()
        correct = [
            {
                'amount': 10,
                'range_end': u'192.168.128.9',
                'range_start': u'192.168.128.0',
                'type': 'free',
            },
            {
                'amount': 2,
                'range_end': u'192.168.128.11',
                'range_start': u'192.168.128.10',
                'type': 'addr',
            },
            {
                'amount': 1268,
                'range_end': u'192.168.132.255',
                'range_start': u'192.168.128.12',
                'type': 'free',
            },
            {
                'amount': 257,
                'range_end': u'192.168.134.0',
                'range_start': u'192.168.133.0',
                'type': self.net4,
            },
            {
                'amount': 31232,
                'range_end': '192.169.0.0',
                'range_start': '192.168.134.1',
                'type': 'free',
            },
        ]
        self.assertEquals(ret, correct)

    def test_get_network_tree(self):
        res = get_network_tree()
        correct = [
            {
                'network': self.net1,
                'subnetworks': [
                    {
                        'network': self.net2,
                        'subnetworks': [],
                    },
                    {
                        'network': self.net3,
                        'subnetworks': [
                            {
                                'network': self.net4,
                                'subnetworks': [],
                            }
                        ]
                    },
                    {
                        'network': self.net4,
                        'subnetworks': [],
                    }
                ]
            },
            {
                'network': self.net5,
                'subnetworks': [],
            }
        ]
        self.assertEquals(res, correct)

    def test_ip_is_public_or_no(self):
        ip_list = [
            ('92.143.123.123', True),
            ('10.168.123.123', False),
        ]
        for ip, is_public in ip_list:
            new_ip_address = IPAddress(address=ip)
            new_ip_address.save()
            self.assertEquals(new_ip_address.is_public, is_public)


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
