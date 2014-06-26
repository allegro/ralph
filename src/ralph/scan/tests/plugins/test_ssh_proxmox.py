# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.test import TestCase

from ralph.discovery.tests.util import MockSSH
from ralph.scan.plugins.ssh_proxmox import (
    _add_prefix,
    _get_proxmox_version,
)


LSB_RELEASE_1 = """
Distributor ID: Debian
Description:    Debian GNU/Linux 5.0.0 (lenny)
Release:    5.0.0
Codename:   lenny
"""
LSB_RELEASE_2 = """
Distributor ID: Debian
Description:    Debian GNU/Linux 6.0.0 (squeeze)
Release:    6.0.0
Codename:   squeeze
"""


class SshProxmoxPluginTest(TestCase):

    def test_add_prefix(self):
        self.assertEqual(
            _add_prefix('command123', 1),
            'sudo command123'
        )
        self.assertEqual(
            _add_prefix('command321', 2),
            'sudo -u www-data command321'
        )

    def test_get_proxmox_version(self):
        ssh = MockSSH([("lsb_release -a", LSB_RELEASE_1)])
        self.assertEqual(
            _get_proxmox_version(ssh),
            1
        )
        ssh = MockSSH([("lsb_release -a", LSB_RELEASE_2)])
        self.assertEqual(
            _get_proxmox_version(ssh),
            2
        )
