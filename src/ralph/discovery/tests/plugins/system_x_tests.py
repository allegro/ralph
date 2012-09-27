# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from mock import patch
from django.test import TestCase
from django.conf import settings

from ralph.discovery.models import Memory, Ethernet, Device
from ralph.discovery.plugins.http_ibm_system_x import (
         _get_model_name, _get_sn, _get_memory,
        _get_mac_addresses, _run_http_ibm_system_x
)
from ralph.discovery.tests.plugins.samples import http_ibm_system_x as data



def _patched_send_soap(post_url, session_id, message):
    if message.find('http://www.ibm.com/iBMC/sp/Monitors/GetVitalProductData')>=0:
        return data.generic_data_response
    elif message.find('http://www.ibm.com/iBMC/sp/iBMCControl/GetSPNameSettings')>=0:
        return data.sn_response
    elif message.find('http://www.ibm.com/iBMC/sp/Monitors/GetMemoryInfo')>=0:
        return data.memory_response
    elif message.find('http://www.ibm.com/iBMC/sp/Monitors/GetHostMacAddresses')>=0:
        return data.macs_response
    else:
        raise Exception('Unknown message type')


def _patched_get_session_id(ip):
    return '65c77c6b-af39-4901-8fef-2dec8c6dd24d'


class SystemXPluginTest(TestCase):
    """ IBM System X Test case """
    def setUp(self):
        settings.IBM_SYSTEM_X_USER = 'test'
        settings.IBM_SYSTEM_X_PASSWORD = 'test'
        self.ip = '10.10.10.10'
        self.session_id = '123'

    @patch('ralph.discovery.plugins.http_ibm_system_x._get_session_id', _patched_get_session_id)
    @patch('ralph.discovery.plugins.http_ibm_system_x._send_soap', _patched_send_soap)
    def test_import(self):
        """ Try to save into the database. Check for fields required.
        """
        _run_http_ibm_system_x(self.ip)
        dev = Device.objects.get(model__name='System x3550 M3')
        self.assertEqual(Memory.objects.filter(device=dev).count(), 8)
        self.assertEqual([(x.model.name, x.label, x.size)
            for x in Memory.objects.filter(device=dev).order_by('-id')],
            [(u'RAM DIMM 18 4096MiB', u'DIMM 18', 4096),
                (u'RAM DIMM 15 8192MiB', u'DIMM 15', 8192),
                (u'RAM DIMM 12 8192MiB', u'DIMM 12', 8192),
                (u'RAM DIMM 11 4096MiB', u'DIMM 11', 4096),
                (u'RAM DIMM 9 4096MiB', u'DIMM 9', 4096),
                (u'RAM DIMM 6 8192MiB', u'DIMM 6', 8192),
                (u'RAM DIMM 3 8192MiB', u'DIMM 3', 8192),
                (u'RAM DIMM 2 4096MiB', u'DIMM 2', 4096)])
        self.assertEqual([(x.label, x.mac)
            for x in Ethernet.objects.filter(device=dev).order_by('-id')],
            [(u'Host Ethernet MAC Address 2', u'6EF3DDE59642'),
            (u'Host Ethernet MAC Address 1', u'6EF3DDE59640')]
        )

    @patch('ralph.discovery.plugins.http_ibm_system_x._get_session_id', _patched_get_session_id)
    @patch('ralph.discovery.plugins.http_ibm_system_x._send_soap', _patched_send_soap)
    def test_soap_methods(self):
        """ Check return values of particular soap methods.
        """
        model_name = _get_model_name(self.ip, self.session_id)
        self.assertEqual(model_name, 'System x3550 M3')
        sn = _get_sn(self.ip, self.session_id)
        self.assertEqual(sn, 'SN# KD55ARA')
        memory = _get_memory(self.ip, self.session_id)
        self.assertEqual(memory, [
            {'index': 2, 'size': 4096, 'label': 'DIMM 2'},
            {'index': 3, 'size': 8192, 'label': 'DIMM 3'},
            {'index': 6, 'size': 8192, 'label': 'DIMM 6'},
            {'index': 9, 'size': 4096, 'label': 'DIMM 9'},
            {'index': 11, 'size': 4096, 'label': 'DIMM 11'},
            {'index': 12, 'size': 8192, 'label': 'DIMM 12'},
            {'index': 15, 'size': 8192, 'label': 'DIMM 15'},
            {'index': 18, 'size': 4096, 'label': 'DIMM 18'}
        ])
        macs = _get_mac_addresses(self.ip, self.session_id)
        self.assertEqual(macs, [['Host Ethernet MAC Address 1', '6E:F3:DD:E5:96:40'],
            ['Host Ethernet MAC Address 2', '6E:F3:DD:E5:96:42']])

