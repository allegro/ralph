#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import paramiko

from ralph.util import plugin, network
from ralph.discovery import storageworks
from django.conf import settings

SSH_MSA_USER = settings.SSH_MSA_USER
SSH_MSA_PASSWORD = settings.SSH_MSA_PASSWORD


def _connect_ssh(ip):
    return network.connect_ssh(ip, SSH_MSA_USER, SSH_MSA_PASSWORD,
                               client=storageworks.HPSSHClient)


def _run_ssh_msa(ip):
    ssh = _connect_ssh(ip)
    return storageworks.run(ssh, ip)


@plugin.register(chain='discovery', requires=['ping', 'http'])
def ssh_hp_msa(**kwargs):
    if SSH_MSA_USER is None or SSH_MSA_PASSWORD is None:
        return False, 'no credentials.', kwargs
    if 'nx-os' in kwargs.get('snmp_name', '').lower():
        return False, 'incompatible Nexus found.', kwargs
    ip = str(kwargs['ip'])
    if kwargs.get('http_family') not in ('WindRiver-WebServer',):
        return False, 'no match.', kwargs
    if not network.check_tcp_port(ip, 22):
        return False, 'closed.', kwargs
    try:
        name = _run_ssh_msa(ip)
    except (network.Error, storageworks.Error) as e:
        return False, str(e), kwargs
    except storageworks.Error as e:
        return False, str(e), kwargs
    except paramiko.SSHException as e:
        return False, str(e), kwargs
    return True, name, kwargs
