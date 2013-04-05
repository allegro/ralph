#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.conf import settings
from django.core.exceptions import MultipleObjectsReturned
from lck.django.common import nested_commit_on_success
from lck.django.common.models import MACAddressField
from paramiko import SSHException

from ralph.discovery.models import Device, DeviceType, IPAddress
from ralph.util import Eth, network, plugin


SAVE_PRIORITY = 5


def get_instances_list(ssh):
    stdin, stdout, stderr = ssh.exec_command(
        "gnt-instance list -o name,pnode,snodes,ip,mac --no-headers",
    )
    for line in stdout.read().strip().splitlines():
        data = line.strip().split()
        yield {
            'host': data[0],
            'primary_node': data[1],
            'secondary_nodes': data[2],
            'ip': data[3] if data[3] != '-' else '',
            'mac': MACAddressField.normalize(data[4]),
        }


def get_hypervisor(name, hypervisors):
    hypervisor = hypervisors.get(name)
    if hypervisor is None:
        try:
            hypervisor = Device.objects.get(name__contains=name)
        except MultipleObjectsReturned:
            try:
                hypervisor = Device.objects.get(name=name)
            except Device.DoesNotExist:
                pass
        hypervisors[name] = hypervisor if hypervisor else False
    return hypervisor


@nested_commit_on_success
def save_device(data, hypervisors):
    hypervisor = get_hypervisor(data['primary_node'], hypervisors)
    ethernets = [Eth(label='eth0', mac=data['mac'], speed=0)]
    dev = Device.create(
        ethernets=ethernets,
        model_name='Ganeti',
        model_type=DeviceType.virtual_server,
        family='Virtualization',
        priority=SAVE_PRIORITY,
    )
    if hypervisor:
        dev.parent = hypervisor
        dev.save(priority=SAVE_PRIORITY)
    if data['ip']:
        ip_address, created = IPAddress.concurrent_get_or_create(
            address=data['ip'],
        )
        ip_address.device = dev
        ip_address.save()


def run_ssh_ganeti(ssh):
    hypervisors = {}
    for host in get_instances_list(ssh):
        save_device(host, hypervisors)


# @plugin.register(chain='discovery', requires=['ping', 'ssh_linux'])
@plugin.register(chain='discovery', requires=['ping'])
def ssh_ganeti(**kwargs):
    # if not kwargs.get('ganeti_master', False):
    #     return False, 'no match', kwargs
    ip = str(kwargs['ip'])
    if not network.check_tcp_port(ip, 22):
        return False, 'closed', kwargs
    ssh = None
    auths = [
        (settings.SSH_USER or 'root', settings.SSH_PASSWORD),
        (settings.XEN_USER, settings.XEN_PASSWORD),
    ]
    try:
        for user, password in auths:
            if user is None or password is None:
                continue
            try:
                ssh = network.connect_ssh(ip, user, password)
            except network.AuthError:
                pass
            else:
                break
        else:
            return False, 'authorization failed', kwargs
        run_ssh_ganeti(ssh)
    except (network.Error, SSHException) as e:
        return False, str(e), kwargs
    return True, 'done', kwargs
