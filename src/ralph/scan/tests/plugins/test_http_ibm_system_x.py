# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.test import TestCase
from mock import patch

from ralph.scan.tests.plugins.samples import http_ibm_system_x as SAMPLES
from ralph.scan.plugins.http_ibm_system_x import _http_ibm_system_x


def _patched_send_soap(post_url, session_id, message):
    if 'http://www.ibm.com/iBMC/sp/Monitors/GetVitalProductData' in message:
        return SAMPLES.GENERIC_DATA_RESPONSE
    elif 'http://www.ibm.com/iBMC/sp/iBMCControl/GetSPNameSettings' in message:
        return SAMPLES.SN_RESPONSE
    elif 'http://www.ibm.com/iBMC/sp/Monitors/GetMemoryInfo' in message:
        return SAMPLES.MEMORY_RESPONSE
    elif 'http://www.ibm.com/iBMC/sp/Monitors/GetHostMacAddresses' in message:
        return SAMPLES.MACS_RESPONSE
    elif 'http://www.ibm.com/iBMC/sp/Monitors/GetProcessorInfo' in message:
        return SAMPLES.PROCESSORS_RESPONSE
    else:
        raise Exception('Unknown message type')


def _patched_get_session_id(ip_address, user, password):
    return '65c77c6b-af39-4901-8fef-2dec8c6dd24d'


class HttpIbmSystemXTest(TestCase):

    @patch(
        'ralph.scan.plugins.http_ibm_system_x._get_session_id',
        _patched_get_session_id,
    )
    @patch(
        'ralph.scan.plugins.http_ibm_system_x._send_soap',
        _patched_send_soap,
    )
    def test_http_ibm_system_x(self):
        self.assertEqual(
            _http_ibm_system_x('127.0.0.1', '-', '-'),
            {
                'mac_addresses': ['6EF3DDE59640', '6EF3DDE59642'],
                'management_ip_address': ['127.0.0.1'],
                'memory': [
                    {'index': 2, 'label': 'DIMM 2', 'size': 4096},
                    {'index': 3, 'label': 'DIMM 3', 'size': 8192},
                    {'index': 6, 'label': 'DIMM 6', 'size': 8192},
                    {'index': 9, 'label': 'DIMM 9', 'size': 4096},
                    {'index': 11, 'label': 'DIMM 11', 'size': 4096},
                    {'index': 12, 'label': 'DIMM 12', 'size': 8192},
                    {'index': 15, 'label': 'DIMM 15', 'size': 8192},
                    {'index': 18, 'label': 'DIMM 18', 'size': 4096},
                ],
                'model_name': 'System x3550 M3',
                'processors': [
                    {
                        'cores': '8',
                        'family': 'Intel Xeon',
                        'index': '1',
                        'label': 'Intel Xeon CPU 2666 MHz, 8 cores 1 threads',
                        'speed': '2666',
                    },
                    {
                        'cores': '8',
                        'family': 'Intel Xeon',
                        'index': '2',
                        'label': 'Intel Xeon CPU 2666 MHz, 8 cores 1 threads',
                        'speed': '2666',
                    },
                ],
                'serial_number': 'SN# KD55ARA',
                'type': 'rack server',
            },
        )
