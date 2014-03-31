# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.test import TestCase
from lck.django.common.models import MACAddressField
from powerdns.models import Domain, Record

from ralph.discovery.models import (
    DataCenter,
    Device,
    DeviceModel,
    DeviceType,
    Environment,
    Ethernet,
    EthernetSpeed,
    IPAddress,
    Network,
    NetworkTerminator,
)
from ralph.business.models import Venture, VentureRole
from ralph.deployment.models import Deployment, ArchivedDeployment
from ralph.deployment.util import (
    get_next_free_hostname, get_first_free_ip, _create_device
)
from ralph.dnsedit.models import DHCPEntry
from ralph.util import Eth


class DeploymentTest(TestCase):

    def setUp(self):
        self.top_venture = Venture(name='top_venture')
        self.top_venture.save()
        self.child_venture = Venture(
            name='child_venture',
            parent=self.top_venture,
        )
        self.child_venture.save()
        self.role = VentureRole(
            name='role',
            venture=self.child_venture,
        )
        self.role.save()
        self.child_role = VentureRole(
            name='child_role',
            venture=self.child_venture,
            parent=self.role,
        )
        self.child_role.save()
        dm = self.add_model('DC model sample', DeviceType.data_center.id)
        self.dc = Device.create(sn='sn1', model=dm)
        self.dc.name = 'dc'
        self.dc.save()
        dm = self.add_model('Rack model sample', DeviceType.rack_server.id)
        self.rack = Device.create(
            venture=self.child_venture,
            sn='sn2',
            model=dm,
        )
        self.rack.parent = self.dc
        self.rack.name = 'rack'
        self.rack.save()
        dm = self.add_model('Blade model sample', DeviceType.blade_server.id)
        self.blade = Device.create(
            venture=self.child_venture,
            venturerole=self.child_role,
            sn='sn3',
            model=dm,
        )
        self.blade.name = 'blade'
        self.blade.parent = self.rack
        self.blade.save()
        self.deployment = Deployment()
        self.deployment.hostname = 'test_host2'
        self.deployment.device = self.blade
        self.deployment.mac = '10:9a:df:6f:af:01'
        self.deployment.ip = '192.168.1.1'
        self.deployment.hostname = 'test'
        self.deployment.save()

    def add_model(self, name, device_type):
        dm = DeviceModel()
        dm.model_type = device_type,
        dm.name = name
        dm.save()
        return dm

    def test_archivization(self):
        id = self.deployment.id
        data = {}
        for field in self.deployment._meta.fields:
            data[field.name] = getattr(self.deployment, field.name)
            if field.name == 'mac':
                data[field.name] = MACAddressField.normalize(data[field.name])
        self.deployment.archive()
        archive = ArchivedDeployment.objects.get(pk=id)
        archive_data = {}
        for field in archive._meta.fields:
            archive_data[field.name] = getattr(archive, field.name)
            if field.name == 'mac':
                archive_data[field.name] = MACAddressField.normalize(
                    archive_data[field.name]
                )
        self.assertEqual(data, archive_data)
        with self.assertRaises(Deployment.DoesNotExist):
            Deployment.objects.get(pk=id)


class DeploymentUtilTest(TestCase):

    def setUp(self):
        # create data centers
        self.dc_temp1 = DataCenter.objects.create(
            name='temp1',
        )
        self.dc_temp2 = DataCenter.objects.create(
            name='temp2',
        )
        self.env_temp1 = Environment.objects.create(
            name='temp1',
            hosts_naming_template='h<100,199>.temp1|h<300,399>.temp1',
            data_center=self.dc_temp1,
        )
        self.env_temp2 = Environment.objects.create(
            name='temp2',
            hosts_naming_template='h<200,299>.temp2',
            data_center=self.dc_temp2,
        )
        # create domains
        self.domain_temp1 = Domain.objects.create(name='temp1')
        self.domain_temp2 = Domain.objects.create(name='temp2')
        # create temp deployment
        dev = Device.create(
            ethernets=[Eth(
                'SomeEthLabel', 'aa11cc2266bb', EthernetSpeed.unknown
            )],
            model_type=DeviceType.unknown,
            model_name='Unknown'
        )
        IPAddress.objects.create(
            address='127.0.1.4',
            device=dev
        )
        Deployment.objects.create(
            device=dev,
            mac='aa11cc2266bb',
            ip='127.0.1.2',
            hostname='h202.temp2'
        )
        # create temp networks
        terminator = NetworkTerminator.objects.create(name='T100')
        net1 = Network.objects.create(
            name='net1',
            address='127.0.1.0/24',
            data_center=self.dc_temp1,
            reserved=1,
            gateway='127.0.0.254',
            environment=self.env_temp1,
        )
        net1.terminators.add(terminator)
        net1.save()
        net2 = Network.objects.create(
            name='net2',
            address='127.0.0.0/24',
            data_center=self.dc_temp1,
            gateway='127.0.0.254',
            environment=self.env_temp1,
        )
        net2.terminators.add(terminator)
        net2.save()
        net3 = Network.objects.create(
            name='net3',
            address='192.168.0.1/28',
            data_center=self.dc_temp1,
            gateway='127.0.0.254',
            environment=self.env_temp1,
        )
        net3.terminators.add(terminator)
        net3.reserved = 1
        net3.reserved_top_margin = 15
        net3.save()

    def test_get_nexthostname(self):
        name = get_next_free_hostname(self.env_temp1)
        self.assertEqual(name, 'h100.temp1')
        name = get_next_free_hostname(self.env_temp2)
        self.assertEqual(name, 'h200.temp2')

        Record.objects.create(
            domain=self.domain_temp1,
            name='h103.temp1',
            content='127.0.1.2',
            type='A',
        )
        name = get_next_free_hostname(self.env_temp1)
        self.assertEqual(name, 'h104.temp1')
        Record.objects.create(
            domain=self.domain_temp1,
            name='h199.temp1',
            content='127.0.1.3',
            type='A',
        )
        name = get_next_free_hostname(self.env_temp1)
        self.assertEqual(name, 'h300.temp1')

        dev = Device.create(
            sn='test_sn_998877',
            model_type=DeviceType.unknown,
            model_name='Unknown'
        )
        dev.name = 'h300.temp1'
        dev.save()
        Record.objects.create(
            domain=self.domain_temp1,
            name='123',
            content='h301.temp1',
            type='PTR',
        )
        name = get_next_free_hostname(self.env_temp1)
        self.assertEqual(name, 'h302.temp1')

        name = get_next_free_hostname(
            self.env_temp2, ['h200.temp2', 'h201.temp2'],
        )
        self.assertEqual(name, 'h203.temp2')

    def test_get_firstfreeip(self):
        ip = get_first_free_ip('net2')
        self.assertEqual(ip, '127.0.0.10')  # first ten addresses are reserved
        Record.objects.create(
            domain=self.domain_temp1,
            name='host123.temp1',
            content='127.0.1.3',
            type='A'
        )
        DHCPEntry.objects.create(
            mac='aa:43:c2:11:22:33',
            ip='127.0.1.5'
        )
        Record.objects.create(
            domain=self.domain_temp1,
            name='6.1.0.127.in-addr.arpa',
            content='host321.temp1',
            type='PTR'
        )
        ip = get_first_free_ip('net1', ['127.0.1.1'])
        # 127.0.1.1 - reserved
        # 127.0.1.2 - deployment
        # 127.0.1.3 - dns (A)
        # 127.0.1.4 - discovery
        # 127.0.1.5 - dhcp
        # 127.0.1.6 - dns (PTR)
        # 127.0.1.7 - should be free
        self.assertEqual(ip, '127.0.1.7')

        ip = get_first_free_ip('net3')
        self.assertEqual(ip, None)  # bad margins...

    def test_create_device(self):
        data = {
            'mac': '18:03:73:b1:85:93',
            'rack_sn': 'rack_sn_123_321_1',
            'management_ip': '10.20.10.1',
            'hostname': 'test123.dc',
            'ip': '10.22.10.1',
        }
        _create_device(data)
        ethernet = Ethernet.objects.get(mac='18:03:73:b1:85:93')
        self.assertEqual(ethernet.label, 'DEPLOYMENT MAC')
        self.assertEqual(ethernet.device.model.type, DeviceType.unknown)
        ip_address = IPAddress.objects.get(
            device=ethernet.device,
            is_management=True,
        )
        self.assertEqual(ip_address.address, '10.20.10.1')
        self.assertTrue(ip_address.is_management)
