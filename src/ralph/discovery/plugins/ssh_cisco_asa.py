#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""SSH-based disco for Cisco ASA firewalls."""


from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import ssh as paramiko
import time

from django.conf import settings
from lck.django.common import nested_commit_on_success

from ralph.util import network, parse, plugin, Eth
from ralph.discovery import guessmodel
from ralph.discovery.cisco import cisco_component, cisco_inventory
from ralph.discovery.models import DeviceType, Device, Ethernet, IPAddress


SSH_USER, SSH_PASS = settings.SSH_SSG_USER, settings.SSH_SSG_PASSWORD


class Error(Exception):
    pass

class ConsoleError(Error):
    pass

class CiscoSSHClient(paramiko.SSHClient):
    """SSHClient modified for Cisco's broken ssh console."""

    def __init__(self, *args, **kwargs):
        super(CiscoSSHClient, self).__init__(*args, **kwargs)
        self.set_log_channel('critical_only')

    def _auth(self, username, password, pkey, key_filenames, allow_agent, look_for_keys):
        self._transport.auth_password(username, password)
        self._asa_chan = self._transport.open_session()
        self._asa_chan.invoke_shell()
        self._asa_chan.sendall('\r\n')
        time.sleep(0.125)
        chunk = self._asa_chan.recv(1024)
        if not '> ' in chunk and not chunk.strip().startswith('asa'):
            raise ConsoleError('Expected system prompt, got %r.' % chunk)

    def asa_command(self, command):
        # XXX Work around random characters appearing at the beginning of the command.
        self._asa_chan.sendall('\b')
        time.sleep(0.125)
        self._asa_chan.sendall(command)
        buffer = ''
        end = command[-32:]
        while not buffer.strip('\b ').endswith(end):
            chunk = self._asa_chan.recv(1024)
            buffer += chunk
        self._asa_chan.sendall('\r\n')
        buffer = ['']
        while True:
            chunk = self._asa_chan.recv(1024)
            lines = chunk.split('\n')
            buffer[-1] += lines[0]
            buffer.extend(lines[1:])
            if '% Invalid input' in buffer:
                raise ConsoleError('Invalid input %r.' % buffer)
            if '> ' in buffer[-1]:
                return buffer[1:-1]

def _connect_ssh(ip, username='root', password=''):
    return network.connect_ssh(ip, SSH_USER, SSH_PASS, client=CiscoSSHClient)

@nested_commit_on_success
def run_ssh_asa(ip):
    ssh = _connect_ssh(ip)
    try:
        lines = ssh.asa_command(
            "show version | grep (^Hardware|Boot microcode|^Serial|address is)")
        raw_inventory = '\n'.join(ssh.asa_command("show inventory"))
    finally:
        ssh.close()

    pairs = parse.pairs(lines=[line.strip() for line in lines])
    sn = pairs.get('Serial Number', None)
    model, ram, cpu = pairs['Hardware'].split(',')
    boot_firmware = pairs['Boot microcode']

    ethernets = []
    for i in xrange(99):
        try:
            junk, label, mac = pairs['%d' % i].split(':')
        except KeyError:
            break
        mac = mac.split(',', 1)[0]
        mac = mac.replace('address is', '')
        mac = mac.replace('.', '').upper().strip()
        label = label.strip()
        ethernets.append(Eth(label, mac, speed=None))

    dev = Device.create(ethernets=ethernets, sn=sn, model_name=model,
                        model_type=DeviceType.firewall,
                        boot_firmware=boot_firmware)
    dev.save(update_last_seen=True)

    inventory = list(cisco_inventory(raw_inventory))
    for inv in inventory:
        cisco_component(dev, inv)

    ipaddr, created = IPAddress.concurrent_get_or_create(address=ip)
    ipaddr.device = dev
    ipaddr.is_management = True
    ipaddr.save()

    for label, mac, speed in ethernets:
        eth, created = Ethernet.concurrent_get_or_create(mac=mac, device=dev)
        eth.label = label
        eth.device = dev
        eth.save()

    return model

@plugin.register(chain='discovery', requires=['ping', 'http'])
def ssh_cisco_asa(**kwargs):
    ip = str(kwargs['ip'])
    kwargs['guessmodel'] = gvendor, gmodel = guessmodel.guessmodel(**kwargs)
    if gvendor != 'Cisco' or gmodel not in ('',):
        return False, 'no match: %s %s' % (gvendor, gmodel), kwargs
    if not network.check_tcp_port(ip, 22):
        return False, 'closed.', kwargs
    try:
        name = run_ssh_asa(ip)
    except (network.Error, Error) as e:
        return False, str(e), kwargs
    except paramiko.SSHException as e:
        return False, str(e), kwargs
    return True, name, kwargs

