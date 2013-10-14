# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import mock

from django.test import TestCase

from ralph.scan.merger import (
    _find_data,
    _get_ranked_plugins_list,
    _get_results_quality,
    merge,
)


class UtilsTest(TestCase):
    def test_get_results_quality(self):
        self.assertEqual(
            _get_results_quality('foo/boo/foo', 'memory'), 1,
        )
        self.assertEqual(
            _get_results_quality('ralph.scan.plugins.puppet', 'disks'), 51,
        )

    def test_get_ranked_plugins_list(self):
        with mock.patch(
            'ralph.scan.merger._get_results_quality',
        ) as mock_get_results_quality:
            mock_get_results_quality.side_effect = [50, 25, 75]
            self.assertEqual(
                _get_ranked_plugins_list(['test1', 'test2', 'test3'], 'foo'),
                [
                    {'quality': 25, 'plugin': 'test2'},
                    {'quality': 50, 'plugin': 'test1'},
                    {'quality': 75, 'plugin': 'test3'},
                ],
            )

    def test_find_data(self):
        sample = [
            {'key_1': 'val_1', 'key_2': 'val_2'},
            {'key_1': 'val_1', 'key_3': 'val_3'},
            {'key_1': 'val_1_1', 'key_2': 'val_2', 'key_3': 'val_3_1'},
        ]
        self.assertIsNone(
            _find_data(sample, {'key_1': 'val_1_2'}),
        )
        self.assertIsNone(
            _find_data(sample, {'key_1': 'val_1', 'key_2': 'val_2_1'}),
        )
        self.assertIsNone(
            _find_data(sample, {'key_1': 'val_1', 'key_4': 'val_4'}),
        )
        self.assertIsNone(
            _find_data(
                sample,
                {'key_1': 'val_1', 'key_3': 'val_3', 'key_4': 'val_4'},
            ),
        )
        self.assertEqual(
            _find_data(sample, {'key_2': 'val_2'}),
            {'key_1': 'val_1', 'key_2': 'val_2'},
        )
        self.assertEqual(
            _find_data(sample, {'key_1': 'val_1_1', 'key_3': 'val_3_1'}),
            {'key_1': 'val_1_1', 'key_2': 'val_2', 'key_3': 'val_3_1'},
        )


class MergerTest(TestCase):
    def setUp(self):
        self.sample = {
            'db': [
                {
                    'serial_number': 'sn1',
                    'param_1': 'value 1 0',
                    'param_db': 'only in db',
                },
            ],
            'plugin_1': [
                {
                    'serial_number': 'sn1',
                    'param_1': 'value 1 1',
                    'param_2': 'value 2 1',
                },
                {
                    'device': 'dev_1',
                    'index': '1',
                    'param_1': 'value 1 1',
                    'param_2': 'value 2 1',
                },
                {
                    'device': 'dev_1',
                    'index': '2',
                    'param_1': 'value 1 1',
                    'param_2': 'value 2 1',
                },
                {
                    'serial_number': 'sn4',
                    'device': 'dev_1',
                    'index': '3',
                    'param_1': 'value 1 1',
                    'param_2': 'value 2 1',
                },
            ],
            'plugin_2': [
                {
                    'serial_number': 'sn1',
                    'param_1': 'value 1 2',
                    'param_2': 'value 2 2',
                },
                {
                    'serial_number': 'sn2',
                    'param_1': 'value 1 2',
                    'param_2': 'value 2 2',
                },
                {
                    'serial_number': 'sn3',
                    'param_1': 'value 1 2',
                    'param_2': 'value 2 2',
                },
                {
                    'serial_number': 'sn4',
                    'param_1': 'value 1 2',
                    'param_2': 'value 2 2',
                    'param_3': 'value 3 2',
                },
            ],
            'plugin_3': [
                {
                    'serial_number': 'sn1',
                    'param_1': 'value 1 3',
                    'param_2': 'value 2 3',
                },
                {
                    'param_1': 'value 1 3 1',
                    'param_2': 'value 2 3 1',
                },
                {
                    'serial_number': 'sn3',
                    'param_1': 'value 1 3',
                    'param_2': 'value 2 3',
                },
                {
                    'device': 'dev_1',
                    'index': '1',
                    'param_1': 'value 1 3',
                    'param_2': 'value 2 3',
                    'param_3': 'value 3 3',
                },
            ],
        }

    def test_merger(self):
        with mock.patch(
            'ralph.scan.merger._get_ranked_plugins_list',
        ) as mock_get_ranked_plugins_list:
            mock_get_ranked_plugins_list.return_value = [
                'plugin_2', 'plugin_3', 'plugin_1',
            ]
            self.assertEqual(
                merge(
                    'foo',
                    self.sample,
                    [('serial_number',), ('device', 'index')],
                ),
                [
                    {
                        'param_1': 'value 1 1',
                        'param_2': 'value 2 1',
                        'param_db': 'only in db',
                        'serial_number': 'sn1',
                    },
                    {
                        'param_1': 'value 1 2',
                        'param_2': 'value 2 2',
                        'serial_number': 'sn2',
                    },
                    {
                        'param_1': 'value 1 3',
                        'param_2': 'value 2 3',
                        'serial_number': 'sn3',
                    },
                    {
                        'device': 'dev_1',
                        'index': '3',
                        'param_1': 'value 1 1',
                        'param_2': 'value 2 1',
                        'param_3': 'value 3 2',
                        'serial_number': 'sn4',
                    },
                    {
                        'device': 'dev_1',
                        'index': '1',
                        'param_1': 'value 1 1',
                        'param_2': 'value 2 1',
                        'param_3': 'value 3 3',
                    },
                    {
                        'device': 'dev_1',
                        'index': '2',
                        'param_1': 'value 1 1',
                        'param_2': 'value 2 1',
                    },
                ],
            )

