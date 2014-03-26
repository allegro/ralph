# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.test import TestCase
from ralph.business.models import Venture, VentureRole
from ralph.discovery.models import Device, DeviceType
from ralph.discovery.models_component import (
    Ethernet, DiskShare, GenericComponent, Processor, Software, ComponentModel,
    DiskShareMount, Memory, FibreChannel, SplunkUsage, Storage, OperatingSystem
)
from ralph.discovery.models_history import HistoryChange
from ralph.discovery.models_network import (
    IPAddress, NetworkTerminator, Network, DataCenter)
from ralph.ui.tests.global_utils import login_as_su

DEVICE = {
    'name': 'SimpleDevice',
    'ip': '10.0.0.1',
    'remarks': 'Very important device',
    'venture': 'SimpleVenture',
    'ventureSymbol': 'simple_venture',
    'venture_role': 'VentureRole',
    'model_name': 'xxxx',
    'position': '12',
    'rack': '14',
    'barcode': 'bc_dev',
    'sn': '0000000001',
    'mac': '00:00:00:00:00:00',
}
DISKSHARE = {
    'device': 'DiskShareSrv',
    'sn': '0000000002',
    'barcode': 'bc_share',
    'wwn': 'DiskShareWWN',
}
GENERIC = {
    'sn': '0000000003',
}
NETWORK = {
    'name': 'SimpleNetwork',
    'address': '10.0.0.1/26',
}
DATACENTER = 'dc1'

COMPONENT = {
    'GenericComponent': '__GenericComponent*',
    'DiskShareMount': '__DiskShareMount*',
    'Processor': '__Processor*',
    'Memory': '__Memory*',
    'Storage': '__Storage*',
    'Fibre': '__Fibre*',
    'Software': '__Ralph*',
    'OS': '__Linux*'
}


class SearchTest(TestCase):

    """
    TODO:
    1. when search return more than 1 result
    2. verification objects in html
    """

    def setUp(self):
        self.client = login_as_su()
        venture = Venture(
            name=DEVICE['venture'], symbol=DEVICE['ventureSymbol']
        )
        venture.save()
        self.venture = venture
        venture_role = VentureRole(
            name=DEVICE['venture_role'], venture=self.venture
        )
        venture_role.save()
        self.venture_role = venture_role
        self.device = Device.create(
            sn=DEVICE['sn'],
            barcode=DEVICE['barcode'],
            remarks=DEVICE['remarks'],
            model_name=DEVICE['model_name'],
            model_type=DeviceType.unknown,
            venture=self.venture,
            venture_role=self.venture_role,
            rack=DEVICE['rack'],
            position=DEVICE['position'],
            dc=DATACENTER,
        )
        self.device.name = DEVICE['name']
        self.device.save()
        self.ip = IPAddress(address=DEVICE['ip'], device=self.device)
        self.ip.save()
        self.db_ip = IPAddress.objects.get(address=DEVICE['ip'])
        self.network_terminator = NetworkTerminator(name='simple_terminator')
        self.network_terminator.save()
        self.network_datacenter = DataCenter(name=DATACENTER)
        self.network_datacenter.save()
        self.network = Network(
            name=NETWORK['name'],
            address=NETWORK['address'],
            data_center=self.network_datacenter,
        )
        self.diskshare_device = Device.create(
            sn=DISKSHARE['sn'],
            barcode=DISKSHARE['barcode'],
            model_name='xxx',
            model_type=DeviceType.storage,
        )
        self.diskshare_device.name = DISKSHARE['device']
        self.diskshare_device.save()
        self.cm_generic = ComponentModel(name='GenericModel')
        self.cm_diskshare = ComponentModel(name='DiskShareModel')
        self.cm_processor = ComponentModel(name='ProcessorModel')
        self.cm_memory = ComponentModel(name='MemoryModel')
        self.cm_storage = ComponentModel(name='ComponentModel')
        self.cm_fibre = ComponentModel(name='FibreChannalMidel')
        self.cm_ethernet = ComponentModel(name='EthernetMidel')
        self.cm_software = ComponentModel(name='SoftwareModel')
        self.cm_splunkusage = ComponentModel(name='SplunkusageModel')
        self.cm_operatingsystem = ComponentModel(name='OperatingSystemModel')
        self.generic_component = GenericComponent(
            device=self.device,
            model=self.cm_generic,
            label=COMPONENT['GenericComponent'],
            sn=GENERIC['sn'],
        )
        self.generic_component.save()
        self.diskshare = DiskShare(
            device=self.device,
            model=self.cm_diskshare,
            share_id=self.device.id,
            size=80,
            wwn=DISKSHARE['wwn'],
        )
        self.diskshare.save()
        self.disksharemount = DiskShareMount.concurrent_get_or_create(
            share=self.diskshare,
            device=self.device,
            defaults={
                'volume': COMPONENT['DiskShareMount'],
            },
        )
        self.processor = Processor(
            device=self.device,
            model=self.cm_processor,
            label=COMPONENT['Processor'],
        )
        self.processor.save()
        self.memory = Memory(
            device=self.device,
            model=self.cm_memory,
            label=COMPONENT['Memory'],
        )
        self.memory.save()
        self.storage = Storage(
            device=self.device,
            model=self.cm_storage,
            label=COMPONENT['Storage'],
        )
        self.storage.save()
        self.fibrechannel = FibreChannel(
            device=self.device,
            model=self.cm_fibre,
            label=COMPONENT['Fibre'],
            physical_id='01234',
        )
        self.fibrechannel.save()
        self.ethernet = Ethernet(
            model=self.cm_ethernet,
            device=self.device,
            mac=DEVICE['mac'],
        )
        self.ethernet.save()
        self.software = Software(
            device=self.device,
            model=self.cm_software,
            label=COMPONENT['Software'],
        )
        self.software.save()
        self.splunkusage = SplunkUsage(
            device=self.device,
            model=self.cm_splunkusage,
        )
        self.splunkusage.save()
        self.operatingsystem = OperatingSystem(
            device=self.device,
            model=self.cm_operatingsystem,
            label=COMPONENT['OS'],
        )
        self.operatingsystem.save()
        # device with strange name...
        self.strange_device = Device.create(
            sn='abcabc123123',
            model_name=DEVICE['model_name'],
            model_type=DeviceType.unknown,
            venture=self.venture,
            venture_role=self.venture_role,
            rack=DEVICE['rack'],
            position=DEVICE['position'],
            dc=DATACENTER,
        )
        self.strange_device.name = 'śćź'
        self.strange_device.save()

    def test_access_to_device(self):
        # User has perm to device list and device details
        device_list = self.client.get('/ui/search/info/')
        self.assertEqual(device_list.status_code, 200)
        url = '/ui/search/info/%s' % self.device.id
        device_details = self.client.get(url, follow=True)
        self.assertEqual(device_details.status_code, 200)

    def test_name_field_old(self):
        # Search objects in response.context
        url = '/ui/search/info/%s' % self.device.id
        device_search = self.client.get(url)
        context = device_search.context['object']
        self.assertEqual(context.name, self.device.name)

    def test_address_or_network_field(self):
        url = '/ui/search/info/%s' % self.device.id
        device_search = self.client.get(url)
        context = device_search.context['object']
        # test ip
        self.assertEqual(context.name, self.device.name)
        ip = context.ipaddress_set.filter(address=DEVICE['ip']).count()
        self.assertTrue(ip > 0)
        # test network
        """
        FIXME - i can`t tests network, i need more info !
        """

    def test_remarks_field(self):
        url = '/ui/search/info/%s' % self.device.id
        device_search = self.client.get(url)
        context = device_search.context['object']
        self.assertEqual(context.remarks, DEVICE['remarks'])

    def test_venture_or_role_field(self):
        url = '/ui/search/info/%s' % self.device.id
        device_search = self.client.get(url)
        context = device_search.context['object']
        self.assertEqual(self.device.venture.name, DEVICE['venture'])
        self.assertEqual(context.venture.name, DEVICE['venture'])
        self.assertEqual(context.venture_role_id, self.venture_role.id)
        self.assertEqual(context.venture.symbol, self.venture.symbol)

    def test_model_field(self):
        url = '/ui/search/info/%s' % self.device.id
        device_search = self.client.get(url)
        context = device_search.context['object']
        self.assertEqual(self.device.model.type, DeviceType.unknown)
        self.assertEqual(context.model.type, DeviceType.unknown)
        self.assertEqual(context.model.name, DEVICE['model_name'])

    def test_component_or_software_field(self):
        url = '/ui/search/info/%s' % self.device.id
        device_search = self.client.get(url)
        context = device_search.context['object']
        processor = context.processor_set.filter(device=self.device.id).count()
        self.assertTrue(processor > 0)

    def test_serial_number_mac_or_wwn_field(self):
        url = '/ui/search/info/%s' % self.device.id
        device_search = self.client.get(url)
        context = device_search.context['object']
        self.assertEqual(self.device.sn, context.sn)
        mac = context.ethernet_set.filter(mac=DEVICE['mac']).count()
        self.assertTrue(mac > 0)
        diskshare = context.diskshare_set.filter(device=self.device.id).count()
        self.assertTrue(diskshare > 0)
        dsm = context.disksharemount_set.filter(device=self.device.id).count()
        self.assertTrue(dsm > 0)

    def test_barcode_field(self):
        url = '/ui/search/info/%s' % self.device.id
        device_search = self.client.get(url, follow=True)
        context = device_search.context['object']
        self.assertEqual(self.device.barcode, DEVICE['barcode'])
        self.assertEqual(context.barcode, DEVICE['barcode'])

    def test_datacenter_rack_or_position_field(self):
        url = '/ui/search/info/%s' % self.device.id
        device_search = self.client.get(url, follow=True)
        context = device_search.context['object']
        self.assertEqual(self.device.position, DEVICE['position'])
        self.assertEqual(context.position, DEVICE['position'])
        self.assertEqual(self.device.rack, DEVICE['rack'])
        self.assertEqual(context.rack, DEVICE['rack'])
        self.assertEqual(self.device.dc, DATACENTER)
        self.assertEqual(context.dc, DATACENTER)

    def test_history_field(self):
        url = '/ui/search/info/%s' % self.device.id
        device_search = self.client.get(url, follow=True)
        context = device_search.context['object']
        db_query = HistoryChange.objects.get(
            device=self.device, new_value=DEVICE['name'],
        )
        object_query = context.historychange_set.get(
            device=self.device, new_value=DEVICE['name'],
        )
        self.assertEqual(db_query.old_value, '')
        self.assertEqual(db_query.new_value, DEVICE['name'])
        self.assertEqual(object_query.old_value, '')
        self.assertEqual(object_query.new_value, DEVICE['name'])

    def test_device_type_field(self):
        url = '/ui/search/info/%s' % self.device.id
        device_search = self.client.get(url, follow=True)
        context = device_search.context['object']
        self.assertEqual(self.device.model.type, DeviceType.unknown.id)
        self.assertEqual(context.model.type, DeviceType.unknown)

    def test_device_name_with_strange_characters(self):
        url = '/ui/search/info/?name=śćź'
        device_search = self.client.get(url, follow=True)
        context = device_search.context['object']
        self.assertEqual(context.name, u'śćź')
