#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import ssh as paramiko

from django.conf import settings
from lck.django.common import nested_commit_on_success
from django.utils import simplejson as json

from ralph.util import network, Eth
from ralph.util import plugin
from ralph.discovery.models import IPAddress
from ralph.discovery.models import Device, DeviceType


XEN_USER = settings.XEN_USER
XEN_PASSWORD = settings.XEN_PASSWORD


class Error(Exception):
    pass


def _connect_ssh(ip):
    return network.connect_ssh(ip, XEN_USER, XEN_PASSWORD)


def _ssh_lines(ssh, command):
    stdin, stdout, stderr = ssh.exec_command(command)
    for line in stdout.readlines():
        yield line

@nested_commit_on_success
def run_ssh_xen(ipaddr, parent):
    ssh = _connect_ssh(ipaddr.address)
    try:
        command = ("""ovsdb-tool query /etc/openvswitch/conf.db """
            """'["Open_vSwitch", {"""
            """ "op": "select","""
            """ "table": "Interface","""
            """ "where": [],"""
            """ "columns": ["external_ids"]"""
            """}]'""")
        # ovsdb-tool query /etc/openvswitch/conf.db '["Open_vSwitch", { "op": "select",  "table": "Interface", "where": [], "columns": ["external_ids"]}]'
        stdin, stdout, stderr = ssh.exec_command(command)
        data = json.loads(stdout.read())
        vms = {}
        for row in data[0]['rows']:
            try:
                ids = dict(row['external_ids'][1])
                vm_id = ids['xs-vm-uuid']
                mac = ids['attached-mac']
            except KeyError:
                continue
            vms[vm_id] = Eth(label='Virtual MAC', mac=mac, speed=0)
    finally:
        ssh.close()

    names = []
    for vm_id, ethernet in vms.iteritems():
        dev = Device.create(ethernets=[ethernet], parent=parent,
                model_type=DeviceType.virtual_server,
                model_name='XEN Virtual Server')
        names.append(dev.name or ethernet.mac)

    return ', '.join(names)

@plugin.register(chain='discovery', requires=['ping', 'snmp'])
def ssh_xen(**kwargs):
    ip = str(kwargs['ip'])
    if XEN_USER is None:
        return False, 'no auth.', kwargs
    if 'xen' not in kwargs.get('snmp_name', ''):
        return False, 'no match.', kwargs
    if not network.check_tcp_port(ip, 22):
        return False, 'closed.', kwargs
    ipaddr = IPAddress.objects.get(address=ip)
    dev = ipaddr.device
    if dev is None:
        return False, 'no device.', kwargs
    try:
        name = run_ssh_xen(ipaddr, dev)
    except (network.Error, Error) as e:
        return False, str(e), kwargs
    except paramiko.SSHException as e:
        return False, str(e), kwargs
    except Error as e:
        return False, str(e), kwargs
    return True, name, kwargs

