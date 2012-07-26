# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import mock
import StringIO


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

