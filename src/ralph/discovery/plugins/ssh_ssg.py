#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""SSH-based disco for IBM BladeCenters."""


from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import paramiko
import time

from django.conf import settings
from lck.django.common import nested_commit_on_success

from ralph.util import network, parse
from ralph.util import plugin, Eth
from ralph.discovery.models import DeviceType, Device, IPAddress


SSH_SSG_USER = settings.SSH_SSG_USER
SSH_SSG_PASSWORD = settings.SSH_SSG_PASSWORD


class Error(Exception):
    pass


class ConsoleError(Error):
    pass


class SSGSSHClient(paramiko.SSHClient):

    """SSHClient modified for SSG's broken ssh console."""

    def __init__(self, *args, **kwargs):
        super(SSGSSHClient, self).__init__(*args, **kwargs)
        self.set_log_channel('critical_only')

    def old_command(self, command):
        stdin, stdout, stderr = self.exec_command(command)
        return stdout.realines()

    def _auth(self, username, password, pkey, key_filenames, allow_agent, look_for_keys):
        self._transport.auth_password(username, password)
        self._ssg_chan = self._transport.open_session()
        self._ssg_chan.invoke_shell()
        self._ssg_chan.sendall('\r\n')
        time.sleep(0.125)
        chunk = self._ssg_chan.recv(1024)
        if '->' not in chunk:
            raise ConsoleError('Expected system prompt, got "%s".' % chunk)

    def ssg_command(self, command):
        """
        IBM's ssh has broken channel handling, so do everything in one
        big channel.
        """

        self._ssg_chan.sendall(command)
        buffer = ''
        while not buffer.endswith(command):
            buffer += self._ssg_chan.recv(1024)
        self._ssg_chan.sendall('\r\n')
        buffer = ['']
        while True:
            chunk = self._ssg_chan.recv(1024)
            lines = chunk.split('\n')
            buffer[-1] += lines[0]
            buffer.extend(lines[1:])
            if '->' in buffer[-1]:
                return buffer[:-1]
            if chunk.endswith('--- more --- '):
                self._ssg_chan.sendall('\n')


def _connect_ssh(ip):
    return network.connect_ssh(ip, settings.SSH_SSG_USER,
                               settings.SSH_SSG_PASSWORD, client=SSGSSHClient)


@nested_commit_on_success
def run_ssh_ssg(ip):
    ssh = _connect_ssh(ip)
    lines = ssh.ssg_command('get system')
    pairs = parse.pairs(lines=lines[:10])
    name = pairs['Product Name']
    version = pairs['Hardware Version'].split(',', 1)[0]
    model = '%s %s' % (name, version)
    mac = pairs['Base Mac'].replace('.', '').upper()
    sn = pairs['Serial Number'].split(',', 1)[0]
    dev = Device.create(
        ethernets=[Eth(label='Base MAC', mac=mac, speed=0)],
        model_name=model,
        model_type=DeviceType.firewall,
        sn=sn,
        name=name,
    )
    dev.boot_firmware = pairs['Software Version'].split(',', 1)[0]
    dev.save(update_last_seen=True)
    ipaddr, created = IPAddress.concurrent_get_or_create(address=ip)
    ipaddr.device = dev
    ipaddr.is_management = True
    ipaddr.save()
    return dev.name


@plugin.register(chain='discovery', requires=['ping', 'http'])
def ssh_ssg(**kwargs):
    if SSH_SSG_USER is None or SSH_SSG_PASSWORD is None:
        return False, 'no credentials.', kwargs
    ip = str(kwargs['ip'])
    if kwargs.get('http_family') not in ('SSG', 'Unspecified'):
        return False, 'no match.', kwargs
    if 'nx-os' in kwargs.get('snmp_name', '').lower():
        return False, 'incompatible Nexus found.', kwargs
    if not network.check_tcp_port(ip, 22):
        return False, 'closed.', kwargs
    try:
        name = run_ssh_ssg(ip)
    except network.Error as e:
        return False, str(e), kwargs
    except Error as e:
        return False, str(e), kwargs
    except paramiko.SSHException as e:
        return False, str(e), kwargs
    return True, name, kwargs
