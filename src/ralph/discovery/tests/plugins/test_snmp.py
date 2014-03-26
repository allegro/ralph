# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.test import TestCase
import mock

from ralph.discovery.plugins import snmp
from ralph.discovery.models import DeviceType, IPAddress


class SnmpPluginTest(TestCase):

    def test_name(self):
        ip = IPAddress(address='127.0.0.1')
        ip.save()
        with mock.patch('ralph.discovery.plugins.snmp.snmp_command') as snmp_command:
            snmp_command.return_value = [[None, b'Testing name']]
            is_up, message = snmp._snmp(
                '127.0.0.1', 'public', (1, 3, 6, 1, 2, 1, 1, 1, 0))
        self.assertEqual(message, 'Testing name')
        self.assertEqual(is_up, True)

    def test_noip(self):
        with mock.patch('ralph.discovery.plugins.snmp.snmp_command') as snmp_command:
            snmp_command.return_value = [[None, b'Testing name']]
            is_up, message = snmp._snmp(
                '127.0.0.1', 'public', (1, 3, 6, 1, 2, 1, 1, 1, 0))
        self.assertEqual(message, 'IP address not present in DB.')
        self.assertEqual(is_up, False)

    def test_silent(self):
        with mock.patch('ralph.discovery.plugins.snmp.snmp_command') as snmp_command:
            snmp_command.return_value = None
            is_up, message = snmp._snmp(
                '127.0.0.1', 'public', (1, 3, 6, 1, 2, 1, 1, 1, 0))
        self.assertEqual(message, 'silent.')
        self.assertEqual(is_up, False)


class SnmpMacPluginTest(TestCase):

    def setUp(self):
        ip = IPAddress(address='127.0.0.1')
        ip.snmp_name = ('Hardware: EM64T Family 6 Model 15 Stepping 7 AT/AT '
                        'COMPATIBLE - Software: Windows Version 5.2 (Build '
                        '3790 Multiprocessor Free)')
        ip.snmp_community = 'public'
        ip.snmp_version = '2c'
        ip.save()
        self.ip = ip
        self.kwargs = {
            'ip': ip.address,
            'community': ip.snmp_community,
            'snmp_name': ip.snmp_name,
            'snmp_version': ip.snmp_version,
        }

    def tearDown(self):
        self.ip.delete()

    def test_windows(self):
        with mock.patch('ralph.discovery.plugins.snmp.snmp_macs') as snmp_macs:
            snmp_macs.return_value = ['001A643320EA']
            ethernets = snmp.do_snmp_mac(self.ip.snmp_name,
                                         self.ip.snmp_community,
                                         self.ip.snmp_version, self.ip.address,
                                         self.kwargs)
        macs = [e.mac for e in ethernets]
        self.assertEquals(macs, ['001A643320EA'])
        ip = IPAddress.objects.get(address=self.ip.address)
        self.assertEquals(ip.is_management, False)
        dev = ip.device
        self.assertNotEquals(dev, None)
        self.assertEquals(dev.model.name, 'Windows')
        self.assertEquals(dev.model.type, DeviceType.unknown.id)
        macs = [e.mac for e in dev.ethernet_set.all()]
        self.assertEquals(macs, ['001A643320EA'])

    def test_windows_empty(self):
        with mock.patch('ralph.discovery.plugins.snmp.snmp_macs') as snmp_macs:
            snmp_macs.return_value = []
            with self.assertRaises(snmp.Error) as raised:
                snmp.do_snmp_mac(self.ip.snmp_name, self.ip.snmp_community,
                                 self.ip.snmp_version, self.ip.address,
                                 self.kwargs)
            self.assertEquals(raised.exception.args[0], 'no MAC.')

    def test_f5(self):
        self.ip.snmp_name = ('Linux f5-2a.dc2 2.6.18-164.11.1.el5.1.0.f5app #1 '
                             'SMP Mon Oct 18 11:55:00 PDT 2010 x86_64')
        self.ip.save()

        def snmp_side(ip, community, oid, *args, **kwargs):
            oid = '.'.join(str(i) for i in oid)
            if oid == '1.3.6.1.4.1.3375.2.1.3.5.2.0':
                return [[None, 'F5 BIG-IP 8400']]
            elif oid == '1.3.6.1.4.1.3375.2.1.3.3.3.0':
                return [[None, 'bip241990s']]
        with mock.patch('ralph.discovery.plugins.snmp.snmp_macs') as snmp_macs:
            snmp_macs.return_value = ['0001D76A7852', '0001D76A7846',
                                      '0001D76A784A', '0001D76A784E', '0001D76A7843', '0001D76A7847',
                                      '0001D76A784B', '0001D76A784F', '0001D76A7844', '0001D76A7848',
                                      '0001D76A784C', '0001D76A7850', '00D06814F5F6', '0001D76A7845',
                                      '0001D76A7849', '0001D76A784D', '0001D76A7851', '0201D76A7851']
            with mock.patch('ralph.discovery.plugins.snmp.snmp_command') as snmp_command:
                snmp_command.side_effect = snmp_side
                snmp.do_snmp_mac(self.ip.snmp_name, self.ip.snmp_community,
                                 self.ip.snmp_version, self.ip.address,
                                 self.kwargs)
        ip = IPAddress.objects.get(address=self.ip.address)
        dev = ip.device
        self.assertNotEquals(dev, None)
        macs = [e.mac for e in dev.ethernet_set.all()]
        self.assertNotIn('0201D76A7851', macs, "Filtering F5 shared MACs.")

    def test_vmware(self):
        self.ip.snmp_name = ('VMware ESX 4.1.0 build-320137 VMware, Inc. '
                             'x86_64')
        self.ip.save()

        def macs_side(ip, community, oid, *args, **kwargs):
            if oid == (1, 3, 6, 1, 4, 1, 6876, 2, 4, 1, 7):
                return ['000C2942346D']
            return ['1CC1DEEC0FEC', '1CC1DEEC0FE8']

        with mock.patch('ralph.discovery.plugins.snmp.snmp_macs') as snmp_macs:
            snmp_macs.side_effect = macs_side
            snmp.do_snmp_mac(self.ip.snmp_name, self.ip.snmp_community,
                             self.ip.snmp_version, self.ip.address, self.kwargs)
        ip = IPAddress.objects.get(address=self.ip.address)
        dev = ip.device
        self.assertNotEquals(dev, None)
        children = [d.model.name for d in dev.child_set.all()]
        self.assertEqual(children, ['VMware ESX virtual server'])
        macs = [
            [e.mac for e in d.ethernet_set.all()] for d in dev.child_set.all()]
        self.assertEqual(macs, [['000C2942346D']])

    def test_modular(self):
        self.ip.snmp_name = 'Intel Modular Server System'
        self.ip.save()

        def macs_side(ip, community, oid, *args, **kwargs):
            soid = '.'.join(str(i) for i in oid)
            if soid.startswith('1.3.6.1.4.1.343.2.19.1.2.10.202.3.1.1.'):
                return {
                    1: set([u'001E670C5960', u'001E67123169', u'001E67123168',
                            u'001E670C5961', u'001E670C53BD', u'001E6710DD9D',
                            u'001E6710DD9C', u'001E670C53BC', u'001E671232F5',
                            u'001E671232F4', u'001E670C5395', u'001E670C5394']),
                    2: set([u'001E670C5960', u'001E670C5961', u'001E670C53BD',
                            u'001E6710DD9D', u'001E6710DD9C', u'001E670C53BC',
                            u'001E671232F5', u'001E671232F4', u'001E670C5395',
                            u'001E670C5394']),
                    3: set([u'001E670C5960', u'001E670C5961', u'001E670C53BD',
                            u'001E6710DD9D', u'001E6710DD9C', u'001E670C53BC',
                            u'001E670C5395', u'001E670C5394']),
                    4: set([u'001E670C5960', u'001E670C5961', u'001E670C53BD',
                            u'001E670C53BC', u'001E670C5395', u'001E670C5394']),
                    5: set([u'001E670C5960', u'001E670C5961', u'001E670C5395',
                            u'001E670C5394']),
                    6: set([u'001E670C5960', u'001E670C5961'])
                }[oid[-1]]
            return ['001E6712C2E6', '001E6712C2E7']
        with mock.patch('ralph.discovery.plugins.snmp.snmp_macs') as snmp_macs:
            snmp_macs.side_effect = macs_side
            with mock.patch('ralph.discovery.plugins.snmp.snmp_command') as snmp_command:
                snmp_command.return_value = [[None, 6]]
                snmp.do_snmp_mac(self.ip.snmp_name, self.ip.snmp_community,
                                 self.ip.snmp_version, self.ip.address, self.kwargs)
        self.maxDiff = None
        ip = IPAddress.objects.get(address=self.ip.address)
        dev = ip.device
        self.assertNotEquals(dev, None)
        children = [d.model.name for d in dev.child_set.all()]
        self.assertEqual(children, ['Intel Modular Blade'] * 6)
        macs = [
            [e.mac for e in d.ethernet_set.all()] for d in dev.child_set.all()]
        self.assertEqual(macs, [
            [u'001E67123168', u'001E67123169'],
            [u'001E671232F4', u'001E671232F5'],
            [u'001E6710DD9C', u'001E6710DD9D'],
            [u'001E670C53BC', u'001E670C53BD'],
            [u'001E670C5394', u'001E670C5395'],
            [u'001E670C5960', u'001E670C5961']
        ])
