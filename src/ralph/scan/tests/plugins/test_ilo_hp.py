# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.test import TestCase

from ralph.discovery.hp_ilo import IloHost
from ralph.scan.plugins.ilo_hp import (
    _get_base_device_info,
    _get_mac_addresses,
    _get_processors,
    _get_memory,
)
from ralph.scan.tests.plugins.samples.ilo_hp import SAMPLE_RIBCL


class IloHpPluginTest(TestCase):

    def setUp(self):
        self.ilo = IloHost('127.0.0.1', '', '')
        self.ilo.update(raw=SAMPLE_RIBCL)

    def test_get_base_device_info(self):
        self.assertEqual(
            _get_base_device_info(self.ilo),
            {
                'model_name': 'HP ProLiant BL2x220c G5',
                'parts': [
                    {
                        'mgmt_firmware': ', Dec 02 2008, rev 1.70',
                        'type': 'management',
                    },
                ],
                'serial_number': 'SN12345678',
                'type': 'blade server',
            },
        )

    def test_get_mac_addresses(self):
        self.assertEqual(
            _get_mac_addresses(self.ilo),
            ['00215AAABB12', '00215AAABB13', '00215AAABB14'],
        )

    def test_get_processors(self):
        self.assertEqual(
            _get_processors(self.ilo),
            [
                {
                    'cores': 4,
                    'family': 'Unknown',
                    'index': 1,
                    'label': 'Proc 1',
                    'model_name': 'CPU Unknown 2500MHz, 4-core',
                    'speed': 2500,
                },
                {
                    'cores': 4,
                    'family': 'Unknown',
                    'index': 2,
                    'label': 'Proc 2',
                    'model_name': 'CPU Unknown 2500MHz, 4-core',
                    'speed': 2500,
                },
            ],
        )

    def test_get_memory(self):
        self.assertEqual(
            _get_memory(self.ilo),
            [
                {
                    'index': 1,
                    'label': 'DIMM 1A',
                    'size': 4096,
                    'speed': 667,
                },
                {
                    'index': 2,
                    'label': 'DIMM 2B',
                    'size': 4096,
                    'speed': 667,
                },
                {
                    'index': 3,
                    'label': 'DIMM 3C',
                    'size': 4096,
                    'speed': 667,
                },
                {
                    'index': 4,
                    'label': 'DIMM 4D',
                    'size': 4096,
                    'speed': 667,
                },
            ],
        )
