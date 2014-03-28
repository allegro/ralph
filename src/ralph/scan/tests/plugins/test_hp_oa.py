# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.test import TestCase
from lck.lang import nullify

from ralph.scan.plugins.hp_oa import _get_parent_device, _handle_subdevices
from ralph.scan.tests.plugins.samples.hp_oa import HP_OA_SAMPLE


HP_OA_SAMPLE = nullify(HP_OA_SAMPLE)


class HpOaPluginTest(TestCase):

    def test_get_parent_device(self):
        self.assertEqual(
            _get_parent_device(HP_OA_SAMPLE),
            {
                'model_name': 'HP BladeSystem c7000 Enclosure G2',
                'rack': 'Rack_208',
                'serial_number': '9B8925V2C9',
                'type': 'blade system',
            },
        )

    def test_handle_subdevices(self):
        sample_device_info = {}
        _handle_subdevices(sample_device_info, HP_OA_SAMPLE)
        self.assertEqual(
            sample_device_info,
            {
                'management_ip_addresses': ['10.235.28.31', '10.235.28.32'],
                'parts': [
                    {
                        'label': 'HP BladeSystem c7000 DDR2 Onboard '
                                 'Administrator with KVM',
                        'model_name': 'HP BladeSystem c7000 DDR2 Onboard '
                                      'Administrator with KVM',
                        'serial_number': 'OB93BP1773',
                        'type': 'management',
                    },
                    {
                        'label': 'HP BladeSystem c7000 DDR2 Onboard '
                                 'Administrator with KVM',
                        'model_name': 'HP BladeSystem c7000 DDR2 Onboard '
                                      'Administrator with KVM',
                        'serial_number': 'OB94BP2794',
                        'type': 'management',
                    },
                ],
                'subdevices': [
                    {
                        'chassis_position': 1,
                        'model_name': 'HP Cisco Catalyst Blade Switch 3020 '
                                      'for HP',
                        'position': '1',
                        'serial_number': 'FOC1316T07G',
                        'type': 'switch',
                    },
                    {
                        'chassis_position': 2,
                        'model_name': 'HP Cisco Catalyst Blade Switch 3020 '
                                      'for HP',
                        'position': '2',
                        'serial_number': 'FOC1316T0D6',
                        'type': 'switch',
                    },
                    {
                        'chassis_position': 3,
                        'model_name': 'HP Brocade 4/24 SAN Switch for HP '
                                      'c-Class BladeSystem',
                        'position': '3',
                        'serial_number': 'CN89197024',
                        'type': 'fibre channel switch',
                    },
                    {
                        'chassis_position': 4,
                        'model_name': 'HP Brocade 4/24 SAN Switch for HP '
                                      'c-Class BladeSystem',
                        'position': '4',
                        'serial_number': 'CN89207019',
                        'type': 'fibre channel switch',
                    },
                    {
                        'chassis_position': 1,
                        'mac_addresses': ['0022649C6FF6', '0022649C7F42'],
                        'model_name': 'HP ProLiant BL460c G1',
                        'position': '1',
                        'serial_number': 'GB8849BBRD',
                        'type': 'blade server',
                    },
                    {
                        'chassis_position': 2,
                        'mac_addresses': ['001A4BD0DC14', '001A4BD0CC0E'],
                        'model_name': 'HP ProLiant BL460c G1',
                        'position': '2',
                        'serial_number': 'CZJ70601RN',
                        'type': 'blade server',
                    },
                    {
                        'chassis_position': 3,
                        'mac_addresses': ['0025B3A31468', '0025B3A3146C'],
                        'model_name': 'HP ProLiant BL460c G6',
                        'position': '3',
                        'serial_number': 'GB8926V80C',
                        'type': 'blade server',
                    },
                    {
                        'chassis_position': 4,
                        'mac_addresses': ['00237DA92A76', '00237DA92A70'],
                        'model_name': 'HP ProLiant BL460c G1',
                        'position': '4',
                        'serial_number': 'GB8908J72D',
                        'type': 'blade server',
                    },
                    {
                        'chassis_position': 5,
                        'mac_addresses': ['001A4BD0B564', '001A4BD0B570'],
                        'model_name': 'HP ProLiant BL460c G1',
                        'position': '5',
                        'serial_number': 'CZJ70601PU',
                        'type': 'blade server',
                    },
                    {
                        'chassis_position': 6,
                        'mac_addresses': ['00237DA92BB0', '00237DA92BB2'],
                        'model_name': 'HP ProLiant BL460c G1',
                        'position': '6',
                        'serial_number': 'GB8908J72R',
                        'type': 'blade server',
                    },
                    {
                        'chassis_position': 7,
                        'mac_addresses': ['002481AEC098', '002481AEC09C'],
                        'model_name': 'HP ProLiant BL460c G6',
                        'position': '7',
                        'serial_number': 'GB8926V807',
                        'type': 'blade server',
                    },
                    {
                        'chassis_position': 8,
                        'mac_addresses': ['0025B3A36D38', '0025B3A36D3C'],
                        'model_name': 'HP ProLiant BL460c G6',
                        'position': '8',
                        'serial_number': 'GB8926V7WH',
                        'type': 'blade server',
                    },
                    {
                        'chassis_position': 9,
                        'mac_addresses': ['0025B3A3A288', '0025B3A3A28C'],
                        'model_name': 'HP ProLiant BL460c G6',
                        'position': '9',
                        'serial_number': 'GB8926V82E',
                        'type': 'blade server',
                    },
                    {
                        'chassis_position': 10,
                        'mac_addresses': ['0025B3A354E0', '0025B3A354E4'],
                        'model_name': 'HP ProLiant BL460c G6',
                        'position': '10',
                        'serial_number': 'GB8926V7X3',
                        'type': 'blade server',
                    },
                    {
                        'chassis_position': 11,
                        'mac_addresses': ['002481AEF178', '002481AEF17C'],
                        'model_name': 'HP ProLiant BL460c G6',
                        'position': '11',
                        'serial_number': 'GB8926V81D',
                        'type': 'blade server',
                    },
                    {
                        'chassis_position': 12,
                        'mac_addresses': ['0025B3A31520', '0025B3A31524'],
                        'model_name': 'HP ProLiant BL460c G6',
                        'position': '12',
                        'serial_number': 'GB8926V800',
                        'type': 'blade server',
                    },
                    {
                        'chassis_position': 13,
                        'mac_addresses': ['002481ADDD08', '002481ADDD0C'],
                        'model_name': 'HP ProLiant BL460c G6',
                        'position': '13',
                        'serial_number': 'GB8926V7XT',
                        'type': 'blade server',
                    },
                    {
                        'chassis_position': 14,
                        'mac_addresses': ['0025B3A37D08', '0025B3A37D0C'],
                        'model_name': 'HP ProLiant BL460c G6',
                        'position': '14',
                        'serial_number': 'GB8926V7XL',
                        'type': 'blade server',
                    },
                    {
                        'chassis_position': 15,
                        'mac_addresses': ['0025B3A31CA0', '0025B3A31CA4'],
                        'model_name': 'HP ProLiant BL460c G6',
                        'position': '15',
                        'serial_number': 'GB8926V7Y9',
                        'type': 'blade server',
                    },
                    {
                        'chassis_position': 16,
                        'mac_addresses': ['0025B3A38390', '0025B3A38394'],
                        'model_name': 'HP ProLiant BL460c G6',
                        'position': '16',
                        'serial_number': 'GB8926V80S',
                        'type': 'blade server',
                    },
                ],
            }
        )
