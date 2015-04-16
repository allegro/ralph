# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from ralph.discovery.models import Device, DeviceModel, DeviceType, Network

from ralph.discovery.tests.util import (
    DeprecatedDataCenterFactory,
    DeprecatedRackFactory,
    DeviceFactory,
    DiscoveryQueueFactory,
    EnvironmentFactory,
    RackServerModelFactory,
)
from ralph.util.demo import DemoData, register
from ralph.discovery.models import DataCenter as DiscoveryDataCenter


@register
class DemoDiscoveryQueue(DemoData):
    name = 'discovery_queue'
    title = 'Discovery queue'

    def generate_data(self, data):
        return {
            'default': DiscoveryQueueFactory.create(name='default'),
        }


@register
class DemoDiscoveryDataCenter(DemoData):
    name = 'discovery_dc'
    title = 'Discovery DC'

    def generate_data(self, data):
        a = DiscoveryDataCenter.objects.create(name='DC A')
        b = DiscoveryDataCenter.objects.create(name='DC B')
        return {
            'a': a,
            'b': b
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
        model = RackServerModelFactory()
        return {
            'device_1': Device.get_or_create_by_mac(
                '02:42:ac:11:ff:ff',
                parent=data['deprecated_dc']['a'],
                dc=data['deprecated_dc']['a'].name,
                rack=data['deprecated_racks']['a'].name,
                service=data['services']['infrastructure'],
                device_environment=data['envs']['prod'],
                model=model,
            )[0],
            'device_2': DeviceFactory(
                parent=data['deprecated_dc']['b'],
                dc=data['deprecated_dc']['b'].name,
                rack=data['deprecated_racks']['b'].name,
                service=data['services']['infrastructure'],
                device_environment=data['envs']['prod'],
                model=model,
            ),
        }


@register
class DemoNetworkEnvs(DemoData):
    name = 'network_envs'
    title = 'Network envs'
    required = ['discovery_queue', 'discovery_dc']

    def generate_data(self, data):
        return {
            'a': EnvironmentFactory.create(
                name='Environment A',
                data_center=data['discovery_dc']['a'],
                queue=data['discovery_queue']['default'],
                hosts_naming_template='h<100,199>.dc',
            ),
            'b': EnvironmentFactory.create(
                name='Environment B',
                data_center=data['discovery_dc']['b'],
                queue=data['discovery_queue']['default'],
                hosts_naming_template='h<200,299>.dc',
            )
        }


@register
class DemoDeviceRack(DemoData):
    name = 'device_racks'
    title = 'Device Racks'

    def generate_data(self, data):
        model = DeviceModel(name='Generic rack', type=DeviceType.rack)
        return {
            'a': DeviceFactory.create(
                model=model,
                sn='S4A2FD39I',
            ),
            'b': DeviceFactory.create(
                model=model,
                sn='D8K9OKD7K',
            ),
            'c': DeviceFactory.create(
                model=model,
                sn='FI8LJ0DA4',
            ),
            'd': DeviceFactory.create(
                model=model,
                sn='U798DA32D',
            ),
        }


@register
class DemoNetworks(DemoData):
    name = 'networks'
    title = 'Networks'
    required = ['device_racks', 'network_envs']

    def generate_data(self, data):
        network_a = Network.objects.create(
            name='Network A',
            address='127.0.0.0/24',
            environment=data['network_envs']['a'],
        )
        network_a.racks.add(data['device_racks']['a'])
        network_a.racks.add(data['device_racks']['c'])

        network_b = Network.objects.create(
            name='Network B',
            address='10.0.0.0/8',
            environment=data['network_envs']['a'],
        )
        network_b.racks.add(data['device_racks']['b'])

        network_c = Network.objects.create(
            name='Network B.1',
            address='10.128.0.0/9',
            environment=data['network_envs']['a']
        )
        network_c.racks.add(data['device_racks']['d'])

        return {
            'a': network_a,
            'b': network_b,
            'c': network_c,
        }
