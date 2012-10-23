# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.test import TestCase
from django.test.client import Client
from ralph.business.models import Venture, VentureRole
from ralph.discovery.models import Device, DeviceType
from ralph.discovery.models_component import Ethernet, DiskShare
from ralph.discovery.models_history import HistoryChange
from ralph.discovery.models_network import (
    IPAddress, NetworkTerminator, Network, DataCenter)

DEVICE_NAME = 'SimpleDevice'
DEVICE_IP = '10.0.0.1'
DEVICE_REMARKS = 'Very important device'

DEVICE_VENTURE = 'SimpleVenture'
DEVICE_VENTURE_SYMBOL = 'simple_venture'
VENTURE_ROLE = 'VentureRole'
DEVICE_POSITION = '12'
DEVICE_RACK = '13'
DEVICE_BARCODE = 'bc_dev'
DEVICE_SN = '0000000001'
DEVICE_MAC = '00:00:00:00:00:00'

DISKSHARE_DEVICE = 'DiskShareSrv'
DISKSHARE_DEVICE_SN = '0000000002'
DISKSHARE_DEVICE_BARCODE = 'bc_share'
WWN = 'DiskShareWWN'

NETWORK_NAME = 'SimpleNetwork'
NETWORK_ADDRESS = '10.0.0.1/26'
DATACENTER = 'dc1'


class TestSearch(TestCase):
    def setUp(self):
        login = 'ralph'
        password = 'ralph'
        user = User.objects.create_user(login, 'ralph@ralph.local', password)
        self.user = user
        self.user.is_staff = True
        self.user.is_superuser = True
        self.user.save()
        self.client = Client()
        self.client.login(username=login, password=password)
        venture = Venture(
            name=DEVICE_VENTURE, symbol=DEVICE_VENTURE_SYMBOL
        )
        venture.save()
        self.venture = venture
        venture_role = VentureRole(name=VENTURE_ROLE, venture=self.venture)
        venture_role.save()
        self.venture_role = venture_role
        self.device = Device.create(
            sn=DEVICE_SN,
            barcode=DEVICE_BARCODE,
            remarks=DEVICE_REMARKS,
            model_name='xxxx',
            model_type=DeviceType.unknown,
            venture=self.venture,
            venture_role=self.venture_role,
            rack=DEVICE_RACK,
            position=DEVICE_POSITION,
            dc=DATACENTER,
        )
        self.device.name = DEVICE_NAME
        self.device.save()
        self.db_device = Device.objects.get(name=self.device.name)
        self.ip = IPAddress(address=DEVICE_IP, device=self.device)
        self.ip.save()
        self.db_ip = IPAddress.objects.get(address=DEVICE_IP)
        self.network_terminator = NetworkTerminator(name='simple_terminator')
        self.network_terminator.save()
        self.network_datacenter = DataCenter(name=DATACENTER)
        self.network_datacenter.save()
        self.network = Network(
            name=NETWORK_NAME,
            address=NETWORK_ADDRESS,
            data_center=self.network_datacenter,
        )
        self.ethernet = Ethernet.concurrent_get_or_create(
            device=self.device, mac=DEVICE_MAC)

        self.diskshare_device = Device.create(
            sn=DISKSHARE_DEVICE_SN,
            barcode=DISKSHARE_DEVICE_BARCODE,
            model_name='xxx',
            model_type=DeviceType.storage,
        )
        self.diskshare_device.name = DISKSHARE_DEVICE
        self.diskshare_device.save()

        self.diskshare = DiskShare(share_id=self.diskshare_device, wwn=WWN)
        self.device_list = self.client.get('/ui/search/info/', follow=True)
        device_url = ('/ui/search/info/%s?name=%s') % (self.device.id,
                                                       self.db_device.name)
        self.response = self.client.get(device_url, follow=True)
        self.object = self.response.context['object']

    def test_access_to_device(self):
        self.assertEqual(self.device_list.status_code, 200)
        self.assertEqual(self.response.status_code, 200)

    def test_name_field(self):
        self.assertEqual(self.db_device.name, DEVICE_NAME)
        self.assertEqual(self.object.name, self.db_device.name)
        self.assertEqual(self.object.barcode, self.db_device.barcode)

    def test_address_or_network_field(self):
        #datapase
        self.assertEqual(self.db_ip.address, DEVICE_IP)
        self.assertEqual(self.db_ip.device.name, DEVICE_NAME)
        #test ip
        self.assertEqual(self.object.name, self.db_device.name)
        self.assertEqual(self.object.ipaddress_set.get().address, DEVICE_IP)
        #test network
        """
        FIXME - i can`t tests network, i need more info !
        """

    def test_remarks_field(self):
        self.assertEqual(self.db_device.remarks, DEVICE_REMARKS)
        self.assertEqual(self.object.remarks, DEVICE_REMARKS)

    def test_venture_or_role_field(self):
        self.assertEqual(self.db_device.venture.name, DEVICE_VENTURE)
        self.assertEqual(self.object.venture.name, DEVICE_VENTURE)
        self.assertEqual(self.object.venture_role_id, self.venture_role.id)

    def test_model_field(self):
        self.assertEqual(self.db_device.model.type, DeviceType.unknown)
        self.assertEqual(self.object.model.type, DeviceType.unknown)

    def test_component_or_software_field(self):
        """
        FIXME - component id amd name
        """
        self.assertEqual('todo', 'done')

    def test_serial_number_mac_or_wwn_field(self):
        self.assertEqual(self.device.sn, DEVICE_SN)
        self.assertEqual(self.object.sn, DEVICE_SN)
        mac = self.device.ethernet_set.get(device=self.device).mac
        self.assertEqual(mac, DEVICE_MAC.replace(':', ''))
        object_query = self.object.ethernet_set.get(device=self.device)
        self.assertEqual(object_query.mac, DEVICE_MAC.replace(':', ''))
        device_url = ('/ui/search/info/%s') % (self.diskshare.share_id.id)
        response = self.client.get(device_url, follow=True)
        object = response.context['object'].diskshare_set.instance.id
#
#        import pdb
#        pdb.set_trace()
#        self.assertEqual(self.device.diskshare, WWN)
#        self.assertEqual(object, DEVICE_SN)

    def test_barcode_field(self):
        self.assertEqual(self.device.barcode, DEVICE_BARCODE)
        self.assertEqual(self.object.barcode, DEVICE_BARCODE)

    def test_datacenter_rack_or_position_field(self):
        self.assertEqual(self.device.position, DEVICE_POSITION)
        self.assertEqual(self.object.position, DEVICE_POSITION)
        self.assertEqual(self.device.rack, DEVICE_RACK)
        self.assertEqual(self.object.rack, DEVICE_RACK)
        self.assertEqual(self.device.dc, DATACENTER)
        self.assertEqual(self.object.dc, DATACENTER)

    def test_history_field(self):
        db_query = HistoryChange.objects.get(
            device=self.device, new_value=DEVICE_NAME,
        )
        object_query = self.object.historychange_set.get(
            device=self.device, new_value=DEVICE_NAME,
        )
        self.assertEqual(db_query.new_value, DEVICE_NAME)
        self.assertEqual(object_query.new_value, DEVICE_NAME)

    def test_device_type_field(self):
        self.assertEqual(self.device.model.type, DeviceType.unknown.id)
        self.assertEqual(self.object.model.type, DeviceType.unknown)
