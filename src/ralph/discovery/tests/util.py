# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import factory
import mock
import StringIO
from uuid import uuid1

import ipaddr
from factory import sequence, Sequence, lazy_attribute, Factory, SubFactory
from factory.django import DjangoModelFactory

from ralph.discovery.models import Ethernet
from ralph.discovery.models_device import (
    Database,
    DatabaseType,
    Device,
    DeviceModel,
    DeviceType,
    LoadBalancerType,
    LoadBalancerVirtualServer,
)
from ralph.cmdb.tests import utils as cmdb_utils
from ralph.discovery.models_network import (
    DiscoveryQueue,
    Environment,
    IPAddress,
    Network,
)
from ralph_assets.models_dc_assets import DeprecatedRalphDC, DeprecatedRalphRack


class DeviceModelFactory(DjangoModelFactory):
    FACTORY_FOR = DeviceModel


class DataCenterModelFactory(DeviceModelFactory):
    name = Sequence(lambda n: 'Data-center-model{}'.format(n))
    type = DeviceType.data_center


class RackModelFactory(DeviceModelFactory):
    name = Sequence(lambda n: 'Rack-model{}'.format(n))
    type = DeviceType.rack


class RackServerModelFactory(DeviceModelFactory):
    name = Sequence(lambda n: 'Rack-server-model{}'.format(n))
    type = DeviceType.rack_server


class DeviceFactory(DjangoModelFactory):
    FACTORY_FOR = Device

    name = Sequence(lambda n: 'Device{}'.format(n))
    service = SubFactory(cmdb_utils.ServiceCatalogFactory)
    device_environment = SubFactory(cmdb_utils.DeviceEnvironmentFactory)
    chassis_position = 1
    position = ''

    @lazy_attribute
    def barcode(self):
        return str(uuid1())


class EthernetFactory(DjangoModelFactory):
    FACTORY_FOR = Ethernet

    device = SubFactory(DeviceFactory)
    mac = "000000000000"


class DeprecatedDataCenterFactory(DjangoModelFactory):
    FACTORY_FOR = DeprecatedRalphDC

    name = Sequence(lambda n: 'DC{}'.format(n))
    model = SubFactory(DataCenterModelFactory)

    @factory.post_generation
    def sn(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            self.sn = extracted
        else:
            self.sn = self.name


class DeprecatedRackFactory(DjangoModelFactory):
    FACTORY_FOR = DeprecatedRalphRack

    name = Sequence(lambda n: 'Rack{}'.format(n))
    model = SubFactory(RackModelFactory)

    @factory.post_generation
    def sn(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            self.sn = extracted
        else:
            self.sn = self.name


class Tenant(object):
    def __init__(self, *args, **kwargs):
        for k, v in kwargs.iteritems():
            setattr(self, k, v)


class TenantFactory(Factory):
    FACTORY_FOR = Tenant

    id = Sequence(lambda n: '12345{}'.format(n))
    name = Sequence(lambda n: 'sample_tenant{}'.format(n))
    description = 'qwerty;asdfg;'
    enabled = True


class NetworkFactory(Factory):
    FACTORY_FOR = Network


class IPAddressFactory(DjangoModelFactory):
    FACTORY_FOR = IPAddress

    @sequence
    def address(n):
        return ipaddr.IPAddress(int(ipaddr.IPAddress('10.1.1.0')) + n)

    @sequence
    def hostname(n):
        return 'host{0}.dc1'.format(n)


class LoadBalancerTypeFactory(DjangoModelFactory):
    FACTORY_FOR = LoadBalancerType

    name = Sequence(lambda n: 'LB Type{}'.format(n))


class LoadBalancerVirtualServerFactory(DjangoModelFactory):
    FACTORY_FOR = LoadBalancerVirtualServer

    name = Sequence(lambda n: 'vip-{}'.format(n))
    service = SubFactory(cmdb_utils.ServiceCatalogFactory)
    device_environment = SubFactory(cmdb_utils.DeviceEnvironmentFactory)
    load_balancer_type = SubFactory(LoadBalancerTypeFactory)
    device = SubFactory(DeviceFactory)
    address = SubFactory(IPAddressFactory)
    port = 80


class DatabaseTypeFactory(DjangoModelFactory):
    FACTORY_FOR = DatabaseType

    name = Sequence(lambda n: 'DB Type{}'.format(n))


class DatabaseFactory(DjangoModelFactory):
    FACTORY_FOR = Database

    service = SubFactory(cmdb_utils.ServiceCatalogFactory)
    device_environment = SubFactory(cmdb_utils.DeviceEnvironmentFactory)
    database_type = SubFactory(DatabaseTypeFactory)
    parent_device = SubFactory(DeviceFactory)
    name = Sequence(lambda n: 'DB{}'.format(n))


class DiscoveryQueueFactory(DjangoModelFactory):
    FACTORY_FOR = DiscoveryQueue

    name = Sequence(lambda n: 'Queue {}'.format(n))


class EnvironmentFactory(DjangoModelFactory):
    FACTORY_FOR = Environment

    name = Sequence(lambda n: 'Environment {}'.format(n))


class MockSSH(object):

    """Utility for mocking the SSHClient objects."""

    class Error(Exception):
        pass

    def __init__(self, data):
        self.data_iter = iter(data)

    def __call__(self, *args, **kwargs):
        return self

    def exec_command(self, command):
        cmd, data = self.data_iter.next()
        if cmd != command:
            raise self.Error("Expected command %r but got %r" % (cmd, command))
        return None, StringIO.StringIO(data), None

    def ssg_command(self, command):
        stdin, stdout, stderr = self.exec_command(command)
        return stdout.readlines()

    def __getattr__(self, name):
        return mock.Mock()
