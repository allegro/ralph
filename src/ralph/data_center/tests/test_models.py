# -*- coding: utf-8 -*-
from ipaddress import ip_address, ip_network

from ddt import data, ddt, unpack
from django.core.exceptions import ValidationError

from ralph.accounts.tests.factories import RegionFactory
from ralph.back_office.models import BackOfficeAsset
from ralph.back_office.tests.factories import WarehouseFactory
from ralph.data_center.models.choices import (
    DataCenterAssetStatus,
    IPAddressStatus,
    Orientation
)
from ralph.data_center.models.networks import IPAddress, Network
from ralph.data_center.models.physical import DataCenterAsset
from ralph.data_center.tests.factories import (
    DataCenterAssetFactory,
    RackFactory
)
from ralph.tests import RalphTestCase


@ddt
class NetworkTest(RalphTestCase):
    def setUp(self):
        self.net1 = Network.objects.create(
            name='net1',
            address='192.168.0.0/16',
        )
        self.net2 = Network.objects.create(
            parent=self.net1,
            name='net2',
            address='192.168.0.0/17',
        )
        self.net3 = Network.objects.create(
            parent=self.net2,
            name='net3',
            address='192.168.128.0/17',
        )
        self.net4 = Network.objects.create(
            parent=self.net3,
            name='net4',
            address='192.168.133.0/24',
        )
        self.net5 = Network.objects.create(
            name='net5',
            address='192.169.133.0/24',
        )

        self.ip1 = IPAddress(address='192.168.128.10')
        self.ip1.save()
        self.ip2 = IPAddress(address='192.168.133.10')
        self.ip2.save()
        self.ip3 = IPAddress(address='192.168.128.11')
        self.ip3.save()

    @unpack
    @data(
        ('net1', 16),
        ('net2', 17),
    )
    def test_get_netmask(self, net, netmask):
        self.assertEquals(getattr(self, net).netmask, netmask)

    @unpack
    @data(
        ('net1', ['net2', 'net3', 'net4']),
        ('net3', ['net4']),
    )
    def test_get_subnetworks(self, net, correct):
        net_obj = getattr(self, net)
        res = net_obj.get_subnetworks()
        self.assertEquals(list(res), list(Network.objects.filter(name__in=correct)))

    @unpack
    @data(
        ('92.143.123.123', True),
        ('10.168.123.123', False),
    )
    def test_ip_is_public_or_no(self, ip, is_public):
        new_ip_address = IPAddress(address=ip)
        new_ip_address.save()
        self.assertEquals(new_ip_address.is_public, is_public)

    @unpack
    @data(
        ('::/128',),
        ('::1/128',),
        ('::/96',),
        ('::ffff:0:0/64',),
        ('2001:7f8::/32',),
        ('2001:db8::/32',),
        ('2002::/24',),
        ('3ffe::/16',),
        ('fd00::/7',),
        ('fe80::/10',),
        ('fec0::/10',),
        ('ff00::/8',),
    )
    def test_network_should_support_ipv6(self, net):
        network = Network(
            name='ipv6 ready',
            address=net,
        )
        self.assertEqual(network.network, ip_network(net, strict=False))

    @unpack
    @data(
        ('192.168.100.0/24', '192.168.100.1', True),
        ('10.1.1.0/24', '10.1.1.1', True),
        ('10.1.1.0/24', '10.1.1.2', True),
        ('10.1.1.0/31', '10.1.1.2', False),
        ('10.1.1.0/31', '10.1.1.1', True),
        ('10.1.1.0/31', '10.1.1.0', True),
    )
    def test_ip_address_should_return_network(self, network, ip, should_return):
        net = Network.objects.create(
            name='ip_address_should_return_network',
            address=network,
        )
        assigned_network = None
        ip = IPAddress.objects.create(address=ip)
        result = ip.get_network()
        if should_return:
            self.assertEqual(net, result)
        else:
            self.assertEqual(None, result)

    @unpack
    @data(
        ('10.1.1.0/24', '10.1.0.255'),
        ('10.1.1.0/24', '10.1.2.0'),
    )
    def test_ip_address_should_not_return_network(self, network, ip):
        net = Network.objects.create(
            name='ip_address_should_return_network',
            address=network,
        )
        ip = IPAddress.objects.create(address=ip, network=None)
        result = ip.get_network()
        self.assertEqual(None, result)

    def test_network_should_return_gateway(self):
        net = Network.objects.create(
            name='ip_address_should_return_gateway',
            address='10.1.1.0/24',
        )
        net.save()
        ip = IPAddress.objects.create(
            address='10.1.1.2',
            is_gateway=True,
            network=net
        )
        self.assertEqual(net.gateway, ip.ip)

    def test_reserve_margin_addresses_should_reserve_free_addresses(self):
        net = Network.objects.create(
            name='ip_address_should_return_network',
            address='10.1.1.0/24',
        )
        ip1 = IPAddress.objects.create(address='10.1.1.1')
        ip2 = IPAddress.objects.create(address='10.1.1.254')
        result = net.reserve_margin_addresses(bottom_count=10, top_count=10)
        self.assertEqual(17, net.ips.filter(status=IPAddressStatus.reserved).count())  # noqa
        self.assertEqual(17, result[0])
        self.assertEqual(set([ip1.number, ip2.number]), result[1])

    def test_create_ip_address(self):
        net = Network.objects.create(
            name='test_create_ip_address',
            address='10.1.1.0/24',
        )
        ip = IPAddress.objects.create(address='10.1.1.0')

    @unpack
    @data(
        ('192.168.1.0/24', 254),
        ('192.168.1.0/30', 2),
        ('192.168.1.0/31', 2),
    )
    def test_net_size(self, addr, size):
        net = Network.objects.create(address=addr)
        self.assertEqual(net.size, size)

    @unpack
    @data(
        ('192.168.1.0/29', ip_address('192.168.1.1'), []),
        ('192.168.1.0/31', ip_address('192.168.1.0'), []),
        ('192.168.1.0/31', ip_address('192.168.1.1'), ['192.168.1.0']),
        ('192.168.1.0/31', None, ['192.168.1.0', '192.168.1.1']),
    )
    def test_get_first_free_ip(self, network_addr, first_free, used):
        net = Network.objects.create(address=network_addr)
        ips = []
        for ip in used:
            IPAddress.objects.create(address=ip, network=net)
        if ips:
            IPAddress.object.bulk_create(ips)
        self.assertEqual(net.get_first_free_ip(), first_free)

    def test_sub_network_should_assign_automatically(self):
        net = Network.objects.create(
            name='net', address='192.168.5.0/24'
        )
        subnet = Network.objects.create(
            name='subnet', address='192.168.5.0/25'
        )
        self.assertEqual(net, subnet.parent)

    def test_sub_network_should_reassign_ip(self):
        ip = IPAddress.objects.create(address='192.169.58.1')
        self.assertEqual(ip.network, None)
        net = Network.objects.create(
            name='net', address='192.169.58.0/24'
        )
        ip.refresh_from_db()
        self.assertEqual(ip.network, net)

    def test_delete_network_shouldnt_delete_related_ip(self):
        net = Network.objects.create(
            name='net', address='192.169.58.0/24'
        )
        ip = IPAddress.objects.create(address='192.169.58.1', network=net)
        net.delete()
        ip.refresh_from_db()
        self.assertTrue(ip)


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
