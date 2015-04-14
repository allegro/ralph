# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from ralph.discovery.tests.util import (
    DeprecatedDataCenterFactory,
    DeprecatedRackFactory,
    DeviceFactory,
    DiscoveryQueueFactory,
)
from ralph.util.demo import DemoData, register


@register
class DemoDiscoveryQueue(DemoData):
    name = 'discovery_queue'
    title = 'Discovery queue'

    def generate_data(self, data):
        return {
            'a': DiscoveryQueueFactory.create(name='Queue A'),
            'b': DiscoveryQueueFactory.create(name='Queue B')
        }


@register
class DemoDeprecatedDataCenter(DemoData):
    name = 'deprecated_dc'
    title = '[Deprecated] DC'
    required = ['discovery_queue', 'services', 'envs']

    def generate_data(self, data):
        return {
            'a': DeprecatedDataCenterFactory(
                name='DC A',
                service=data['services']['infrastructure'],
                device_environment=data['envs']['prod'],
            ),
            'b': DeprecatedDataCenterFactory(
                name='DC B',
                service=data['services']['infrastructure'],
                device_environment=data['envs']['prod'],
            ),
        }


@register
class DemoDeprecatedRack(DemoData):
    name = 'deprecated_racks'
    title = '[Deprecated] Rack'
    required = ['deprecated_dc', 'services', 'envs']

    def generate_data(self, data):
        return {
            'a': DeprecatedRackFactory(
                parent=data['deprecated_dc']['a'],
                dc=data['deprecated_dc']['a'].name,
                service=data['services']['infrastructure'],
                device_environment=data['envs']['prod'],
            ),
            'b': DeprecatedRackFactory(
                parent=data['deprecated_dc']['b'],
                dc=data['deprecated_dc']['b'].name,
                service=data['services']['infrastructure'],
                device_environment=data['envs']['prod'],
            ),
        }


@register
class DemoDevices(DemoData):
    name = 'devices'
    title = 'Devices'
    required = ['deprecated_dc', 'deprecated_racks', 'services', 'envs']

    def generate_data(self, data):
        return {
            'device_1': DeviceFactory(
                parent=data['deprecated_dc']['a'],
                dc=data['deprecated_dc']['a'].name,
                rack=data['deprecated_racks']['a'].name,
                service=data['services']['infrastructure'],
                device_environment=data['envs']['prod'],
            ),
            'device_2': DeviceFactory(
                parent=data['deprecated_dc']['b'],
                dc=data['deprecated_dc']['b'].name,
                rack=data['deprecated_racks']['b'].name,
                service=data['services']['infrastructure'],
                device_environment=data['envs']['prod'],
            ),
        }
