# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import mock
import StringIO
from uuid import uuid1

from factory import Sequence, lazy_attribute, Factory
from factory.django import DjangoModelFactory

from ralph.discovery.models_device import Device


class DeviceFactory(DjangoModelFactory):
    FACTORY_FOR = Device

    name = Sequence(lambda n: 'Device#{}'.format(n))

    @lazy_attribute
    def barcode(self):
        return str(uuid1())


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
