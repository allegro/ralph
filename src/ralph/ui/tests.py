# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.test import TestCase
from django.test.client import Client


############################################
from ralph.discovery.models import Device, DeviceType
from ralph.business.models import Venture
from django.contrib.auth.models import User
from ralph.discovery.models_network import IPAddress, NetworkTerminator, DataCenter, Network

DEVICE_NAME = 'SimpleDevice'
DEVICE_IP = '10.0.0.1'
DEVICE_REMARKS = 'Very important device'

NETWORK_NAME = 'SimpleNetwork'
NETWORK_ADDRESS = '10.0.0.1/26'

class TestSearch(TestCase):
    def setUp(self):
        """
        User configuration
        """
        login = 'ralph'
        password = 'ralph'
        email = 'ralph@ralph.local'
        self.user = User.objects.create_user(login, email, password)
        self.user.is_staff = True
        self.user.is_superuser = True
        self.user.save()
        self.client = Client()
        self.client.login(username = login, password = password)
        """
        Create device
        """
        self.device = Device.create(
            sn = '0000000001',
            barcode = '0000000002',
            remarks = DEVICE_REMARKS,
            model_name='xxx',
            model_type=DeviceType.unknown,
        )
        self.device.name = DEVICE_NAME
        self.device.save()
        self.db_device = Device.objects.get(name = self.device.name)
        """
        Create IPAddress
        """
        self.ip = IPAddress(address = DEVICE_IP, device = self.device)
        self.ip.save()
        self.db_ip = IPAddress.objects.get(address = DEVICE_IP)
        """
        Create Network
        """
        self.network_terminator = NetworkTerminator(name = 'simple_terminator')
        self.network_terminator.save()
        self.network_datacenter = DataCenter(name = 'dc1')
        self.network_datacenter.save()
        self.network = Network(
            name = NETWORK_NAME,
            address = NETWORK_ADDRESS,
            data_center = self.network_datacenter,
#            terminators = self.network_terminator,
        )
        """
        More configuration
        """
        self.device_list = self.client.get('/ui/search/info/', follow=True)
        device_url = ('/ui/search/info/%s?name=%s') % (self.device.id, self.db_device.name)
        self.response = self.client.get(device_url, follow=True)

    def test_name_field(self):
        self.assertEqual(self.db_device.name, DEVICE_NAME)
        self.assertEqual(self.device_list.status_code, 200)
        self.assertEqual(self.response.status_code, 200)
        self.assertEqual(self.response.context['object'].name, self.db_device.name)
        self.assertEqual(self.response.context['object'].barcode, self.db_device.barcode)

    def test_address_or_network_field(self):
        #datapase
        self.assertEqual(self.db_ip.address, DEVICE_IP)
        self.assertEqual(self.db_ip.device.name, DEVICE_NAME)
        self.assertEqual(self.device_list.status_code, 200)
        #test ip
        self.assertEqual(self.response.status_code, 200)
        self.assertEqual(self.response.context['object'].name, self.db_device.name)
        self.assertEqual(self.response.context['object'].ipaddress_set.get().address, DEVICE_IP)
        #test network
        """
        FIXME - i can`t tests network, i need more info !
        """

    def test_remarks_field(self):
        self.assertEqual(self.db_device.remarks, DEVICE_REMARKS)
        self.assertEqual(self.device_list.status_code, 200)
        self.assertEqual(self.response.status_code, 200)

#    def test_venture_or_role_field(self):
#
#    def test_model_field(self):
#
#    def test_component_or_software_field(self):
#
#    def test_serial_number_mac_or_wwn_field(self):
#
#    def test_barcode_or_wwn_field(self):
#
#    def test_datacenter_rack_or_position_field(self):
#
#    def test_history_field(self):
#
#    def test_device_type_field(self):
