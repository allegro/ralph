# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from ralph.discovery.models import (
    DataCenter as DiscoveryDataCenter,
    Device,
    DeviceModel,
    DeviceType,
    Network,
)
from ralph.discovery.tests.util import (
    DatabaseFactory,
    DatabaseTypeFactory,
    DeprecatedDataCenterFactory,
    DeprecatedRackFactory,
    DeviceFactory,
    DeviceModelFactory,
    DiscoveryQueueFactory,
    EnvironmentFactory,
    LoadBalancerTypeFactory,
    LoadBalancerVirtualServerFactory,
    RackServerModelFactory,
)
from ralph.util.demo import DemoData, register


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
                service=data['services']['backup_systems'],
                device_environment=data['envs']['prod'],
            ),
            'b': DeprecatedDataCenterFactory(
                name='DC B',
                service=data['services']['backup_systems'],
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
                service=data['services']['backup_systems'],
                device_environment=data['envs']['prod'],
            ),
            'b': DeprecatedRackFactory(
                parent=data['deprecated_dc']['b'],
                dc=data['deprecated_dc']['b'].name,
                service=data['services']['backup_systems'],
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
                service=data['services']['backup_systems'],
                device_environment=data['envs']['prod'],
                model=model,
            )[0],
            'device_2': DeviceFactory(
                parent=data['deprecated_dc']['b'],
                dc=data['deprecated_dc']['b'].name,
                rack=data['deprecated_racks']['b'].name,
                service=data['services']['databases'],
                device_environment=data['envs']['prod'],
                model=model,
            ),
            'device_3': DeviceFactory(
                parent=data['deprecated_dc']['b'],
                dc=data['deprecated_dc']['b'].name,
                rack=data['deprecated_racks']['b'].name,
                service=data['services']['load_balancing'],
                device_environment=data['envs']['prod'],
                model=DeviceModelFactory(
                    name='F5',
                    type=DeviceType.load_balancer
                ),
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
        model = DeviceModel.objects.create(
            name='Generic rack',
            type=DeviceType.rack
        )
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


@register
class DemoVirtuals(DemoData):
    name = 'virtual'
    title = 'Virtual servers'
    required = ['devices', 'services', 'envs']

    def generate_data(self, data):
        from itertools import cycle
        services = cycle([data['services']['backup_systems'], data['services']['databases']])
        envs = cycle(list(data['envs'].values()))
        model = DeviceModel.objects.create(name='XEN', type=DeviceType.virtual_server)
        result = {}
        for i in range(5):
            result['virtual_{}'.format(i)] = DeviceFactory(
                model=model,
                service=services.next(),
                device_environment=envs.next(),
                parent=data['devices']['device_1'],
                name='XEN-{}'.format(i),
            )
        return result


@register
class DemoTenants(DemoData):
    name = 'tenants'
    title = 'OpenStack Tenants'
    required = ['services', 'envs']

    def generate_data(self, data):
        from uuid import uuid1
        from itertools import cycle
        services = cycle([data['services']['backup_systems'], data['services']['databases']])
        envs = cycle(list(data['envs'].values()))
        model = DeviceModel.objects.create(
            name='OpenStack Juno Tenant',
            type=DeviceType.cloud_server
        )
        result = {}
        for i in range(5):
            result['tenant_{}'.format(i)] = DeviceFactory(
                model=model,
                service=services.next(),
                device_environment=envs.next(),
                sn='openstack-{}'.format(uuid1()),
                name='Tenant-{}'.format(i),
            )
        return result


@register
class DemoVIPs(DemoData):
    name = 'vips'
    title = 'VIPs'
    required = ['services', 'envs', 'devices']

    def generate_data(self, data):
        from itertools import cycle
        services = cycle([data['services']['backup_systems'], data['services']['databases']])
        envs = cycle(list(data['envs'].values()))
        lb_type = LoadBalancerTypeFactory(name='F5')
        result = {}
        for i in range(5):
            result['vip_{}'.format(i)] = LoadBalancerVirtualServerFactory(
                load_balancer_type=lb_type,
                service=services.next(),
                device_environment=envs.next(),
                device=data['devices']['device_3'],
            )
        return result


@register
class DemoDatabases(DemoData):
    name = 'databases'
    title = 'Databases'
    required = ['services', 'envs', 'devices']

    def generate_data(self, data):
        from itertools import cycle
        services = cycle([data['services']['backup_systems'], data['services']['load_balancing']])
        envs = cycle(list(data['envs'].values()))
        db_type = DatabaseTypeFactory(name='Oracle')
        result = {}
        for i in range(5):
            result['database_{}'.format(i)] = DatabaseFactory(
                database_type=db_type,
                service=services.next(),
                device_environment=envs.next(),
                parent_device=data['devices']['device_2'],
            )
        return result
