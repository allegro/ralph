#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import ssh as paramiko
import logging

from django.conf import settings

from ralph.util import network
from ralph.util import plugin, Eth
from ralph.discovery.models import (DeviceType, Device, DiskShare,
                                    DiskShareMount)
from ralph.discovery.hardware import (get_disk_shares, parse_smbios,
                                      handle_smbios)
from ralph.discovery import guessmodel


SAVE_PRIORITY=5
logger = logging.getLogger(__name__)


def run_ssh_linux(ssh, ip):
    # Create the device
    stdin, stdout, stderr = ssh.exec_command(
            "/usr/bin/sudo /usr/sbin/ip addr show | /bin/grep 'link/ether'")
    ethernets = [
        Eth(label='', mac=line.split(None, 3)[1], speed=0)
        for line in stdout
    ]
    dev = Device.create(ethernets=ethernets, model_name='Linux',
                        model_type=DeviceType.unknown)
    dev.save(update_last_seen=True, priority=SAVE_PRIORITY)
    # Add remote disk shares
    wwns = []
    for lv, (wwn, size) in get_disk_shares(ssh).iteritems():
        share = DiskShare.objects.get(wwn=wwn)
        wwns.append(wwn)
        mount, created = DiskShareMount.concurrent_get_or_create(
                share=share, device=dev)
        mount.size = size
        if not mount.volume:
            mount.volume = lv
        mount.save()
    for ds in dev.disksharemount_set(
            is_virtual=False).exclude(share__wwn__in=wwns):
        ds.delete()
    # Handle smbios data
    stdin, stdout, stderr = ssh.exec_command(
            "/usb/bin/sudo /usr/sbin/smbios")
    smb = parse_smbios(stdin.read())
    handle_smbios(dev, smb, priority=SAVE_PRIORITY)


@plugin.register(chain='discovery', requires=['ping', 'snmp'])
def ssh_linux(**kwargs):
    kwargs['guessmodel'] = gvendor, gmodel = guessmodel.guessmodel(**kwargs)
    if gmodel not in {'Linux', 'ESX'}:
        return False, 'no match: %s %s' % (gvendor, gmodel), kwargs
    ip = str(kwargs['ip'])
    if not network.check_tcp_port(ip, 22):
        return False, 'closed.', kwargs
    ssh = None
    auths = [
        ('root', settings.SSH_PASSWORD),
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
            return False, 'Authorization failed', kwargs
        name = run_ssh_linux(ssh, ip)
    except (network.Error, paramiko.SSHException) as e:
        return False, str(e), kwargs
    return True, name, kwargs

