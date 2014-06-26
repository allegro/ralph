# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.test import TestCase
from mock import Mock

from ralph.scan.plugins.ipmi import (
    IPMITool,
    _clean,
    _get_base_info,
    _get_components,
    _get_ipmi_fru,
    _get_mac_addresses,
)
from ralph.scan.tests.plugins.samples.ipmi import (
    IPMI_FRU_SAMPLE,
    IPMI_LAN_SAMPLE,
)


SAMPLES_MAPPER = {
    ('fru', 'print'): IPMI_FRU_SAMPLE,
    ('lan', 'print'): IPMI_LAN_SAMPLE,
}


class IpmiPluginTest(TestCase):

    def setUp(self):
        self.ipmitool = IPMITool('127.0.0.1', 'test', 'test')

        def side_effect(command, subcommand, *args):
            return SAMPLES_MAPPER[(command, subcommand)]
        self.ipmitool.command = Mock(side_effect=side_effect)

    def test_clean(self):
        self.assertEqual(_clean(''), ('', False))
        self.assertEqual(_clean('a .:-_0'), ('a', True))
        self.assertEqual(_clean(' .:-_0'), (' .:-_0', False))

    def test_get_ipmi_fru(self):
        fru = _get_ipmi_fru(self.ipmitool)
        self.assertEqual(
            fru.get('/SYS', {}),
            {
                None: 'FRU Device Description',
                'Board Extra': 'X4170/4270/4275',
                'Board Mfg Date': 'Mon Jan  1 00:00:00 1996',
                'Board Part Number': '501-0000-00',
                'Board Product': 'ASSY,MOTHERBOARD,X4170/X4270/X4275',
                'Board Serial': '9328MSL-09304H08AA',
                'Product Extra': '080020FFFFFFFFFFFFFF00114FE19261',
                'Product Manufacturer': 'ORACLE CORPORATION',
                'Product Name': 'SUN FIRE X4270 SERVER',
                'Product Part Number': '4457000-6',
                'Product Serial': '0932XF707A',
            },
        )
        self.assertEqual(
            fru.get('MB/P0/D5'),
            {
                None: 'FRU Device Description',
                'Product Manufacturer': 'SAMSUNG',
                'Product Name': '4GB DDR3 SDRAM 666',
                'Product Part Number': 'M493B5170EH1-CH9',
                'Product Serial': '942212FE',
                'Product Version': '00',
            },
        )
        self.assertEqual(
            fru.get('SP/NET1', {}),
            {
                None: 'FRU Device Description',
                'Product Manufacturer': 'ASPEED',
                'Product Name': 'ETHERNET CONTROLLER',
                'Product Part Number': 'AST2100',
                'Product Serial': '00:11:4f:e7:92:69',
            },
        )

    def test_get_base_info(self):
        self.assertEqual(
            _get_base_info(
                {
                    None: 'FRU Device Description',
                    'Board Extra': 'X4170/4270/4111',
                    'Board Mfg Date': 'Mon Jan  1 00:00:00 1997',
                    'Board Part Number': '501-0000-11',
                    'Board Product': 'ASSY,MOTHERBOARD,X4170/X4270/X4211',
                    'Board Serial': '9328MSL-09304H08BB',
                    'Product Extra': '080020FFFFFFFFAFFFFF00114FE19222',
                    'Product Manufacturer': 'Mega Corp',
                    'Product Name': 'SUN FIRE X4270 SERVER',
                    'Product Part Number': '4457020-1',
                    'Product Serial': '0832EF707B',
                },
            ),
            {
                u'model_name': u'SUNFIREX427SERVER',
                u'serial_number': u'832EF77B',
                u'type': u'rack server',
            },
        )

    def test_get_mac_addresses(self):
        fru = _get_ipmi_fru(self.ipmitool)
        self.assertEqual(
            _get_mac_addresses(self.ipmitool, fru),
            ['00114FE79269', '3322110D54A3'],
        )

    def test_get_components(self):
        fru = _get_ipmi_fru(self.ipmitool)
        processors, memory = _get_components(fru)
        self.assertEqual(
            processors,
            [
                {
                    'family': 'Intel(R) Xeon(R) Cpu L5520 @ 2.27Ghz',
                    'index': 1,
                    'label': 'Intel(R) Xeon(R) Cpu L5520 @ 2.27Ghz',
                    'model_name': (
                        'CPU Intel(R) Xeon(R) Cpu L5520 @ '
                        '2.27Ghz 2270MHz'
                    ),
                    'speed': 2270,
                },
            ],
        )
        self.assertEqual(
            memory,
            [
                {'index': 1, 'label': '4GB DDR3 SDRAM 666', 'size': 4096},
                {'index': 2, 'label': '4GB DDR3 SDRAM 666', 'size': 4096},
                {'index': 3, 'label': '4GB DDR3 SDRAM 666', 'size': 4096},
                {'index': 4, 'label': '4GB DDR3 SDRAM 666', 'size': 4096},
                {'index': 5, 'label': '4GB DDR3 SDRAM 666', 'size': 4096},
                {'index': 6, 'label': '4GB DDR3 SDRAM 666', 'size': 4096},
            ],
        )
