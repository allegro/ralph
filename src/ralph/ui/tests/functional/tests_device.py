# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.core.urlresolvers import reverse
from django.test import TestCase
from ralph.ui.tests.global_utils import login_as_su
from ralph.discovery.models import Device, DeviceType, IPAddress
from ralph.discovery.models_component import Software
from ralph.discovery.tests.util import DeviceFactory, IPAddressFactory


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

DATACENTER = 'dc1'


class DeviceViewTest(TestCase):

    def setUp(self):
        self.client = login_as_su()
        self.device = Device.create(
            sn=DEVICE['sn'],
            barcode=DEVICE['barcode'],
            remarks=DEVICE['remarks'],
            model_name=DEVICE['model_name'],
            model_type=DeviceType.unknown,
            rack=DEVICE['rack'],
            position=DEVICE['position'],
            dc=DATACENTER,
        )
        self.software1 = Software.create(
            dev=self.device,
            path='apache2',
            model_name='apache2 2.4.3',
            label='apache',
            family='http servers',
            version='2.4.3',
            priority=69,
        )
        self.software2 = Software.create(
            dev=self.device,
            path='gcc',
            model_name='gcc 4.7.2',
            label='gcc',
            family='compilers',
            version='4.7.2',
            priority=69,
        )

    def test_software(self):
        url = '/ui/search/software/{}'.format(self.device.id)
        response = self.client.get(url, follow=False)
        dev = response.context_data['object']
        software = dev.software_set.all()
        self.assertEqual(software[0], self.software1)
        self.assertEqual(software[1], self.software2)


class EditAddressesTest(TestCase):
    """Tests for the device addresses form."""

    def setUp(self):
        self.device = DeviceFactory()
        self.regular_ipaddr = IPAddressFactory()
        self.management_ipaddr = IPAddressFactory(is_management=True)
        self.device.ipaddress_set.add(self.regular_ipaddr)
        self.device.ipaddress_set.add(self.management_ipaddr)
        self.url = reverse('search', kwargs={
            'details': 'addresses',
            'device': str(self.device.pk),
        })
        self.client = login_as_su()
        

    def test_regular_shown(self):
        """Regular IP is shown in form."""
        response = self.client.get(self.url)
        self.assertIn(
            unicode(self.regular_ipaddr.address),
            response.context['ipformset'].as_table(),
        )

    def test_management_not_shown(self):
        """Regular IP is shown in form."""
        response = self.client.get(self.url)
        self.assertNotIn(
            unicode(self.management_ipaddr.address),
            response.context['ipformset'].as_table(),
        )

    def test_edit_via_form(self):
        """You can add regular IP address via form."""
        other_address = IPAddressFactory()
        other_address.save()
        data = {
            'ip': 'Save',
            'ip-0-address': self.regular_ipaddr.address,
            'ip-0-hostname': self.regular_ipaddr.hostname,
            'ip-0-id': self.regular_ipaddr.id,
            'ip-1-address': other_address.address,
            'ip-1-hostname': 'hostname.dc1',
            'ip-1-id': '',
            'ip-INITIAL_FORMS': '1',
            'ip-TOTAL_FORMS': '2',
        }
        self.client.post(self.url, data)
        other_address = IPAddress.objects.get(pk=other_address.pk)
        self.assertEquals(other_address.hostname, 'hostname.dc1')
        self.assertIn(other_address, self.device.ipaddress_set.all())

    def test_try_edit_management_via_form(self):
        """You can't add management IP address via form."""
        other_address = IPAddressFactory(is_management=True)
        other_address.save()
        data = {
            'ip': 'Save',
            'ip-0-address': self.regular_ipaddr.address,
            'ip-0-hostname': self.regular_ipaddr.hostname,
            'ip-0-id': self.regular_ipaddr.id,
            'ip-1-address': other_address.address,
            'ip-1-hostname': 'hostname.dc1',
            'ip-1-id': '',
            'ip-INITIAL_FORMS': '1',
            'ip-TOTAL_FORMS': '2',
        }
        response=self.client.post(self.url, data)
        self.assertContains(
            response,
            'To assign management IP to this device use the linked asset'
        )
        self.assertNotIn(other_address, self.device.ipaddress_set.all())

