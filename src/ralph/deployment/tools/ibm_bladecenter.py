#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.conf import settings

from ralph.scan.plugins.ssh_ibm_bladecenter import IBMSSHClient
from ralph.util import network


def _connect_ssh(ip):
    return network.connect_ssh(
        ip,
        settings.SSH_IBM_USER,
        settings.SSH_IBM_PASSWORD,
        client=IBMSSHClient,
    )


def ssh_ibm_reboot(ip, bay):
    ssh = _connect_ssh(ip)
    command = "power -cycle -T system:blade[%s]" % bay
    result = ssh.ibm_command(command)
    return len(result) > 1 and result[1] and result[1].strip().lower() == 'ok'
