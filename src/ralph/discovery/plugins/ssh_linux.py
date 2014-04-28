#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import paramiko

from django.conf import settings

from ralph.util import network
from ralph.util import plugin, Eth
from ralph.discovery.models import (DeviceType, Device, DiskShare,
                                    DiskShareMount, IPAddress,
                                    OperatingSystem)
from ralph.discovery.hardware import (get_disk_shares, parse_dmidecode,
                                      handle_dmidecode, DMIDecodeError)
from ralph.discovery import guessmodel


SAVE_PRIORITY = 5


def get_ethernets(ssh):
    """Get the MAC addresses"""

    stdin, stdout, stderr = ssh.exec_command(
        "/sbin/ip addr show | /bin/grep 'link/ether'")
    ethernets = [
        Eth(label='', mac=line.split(None, 3)[1], speed=0)
        for line in stdout
    ]
    return ethernets


def run_dmidecode(ssh, ethernets):
    """Handle dmidecode data"""

    stdin, stdout, stderr = ssh.exec_command(
        "/usr/bin/sudo /usr/sbin/dmidecode")
    try:
        info = parse_dmidecode(stdout.read())
    except (DMIDecodeError, IOError):
        # No dmidecode, fall back to dumb device
        if not ethernets:
            # No serial number and no macs -- no way to make a device
            return None
        dev = Device.create(ethernets=ethernets, model_name='Linux',
                            model_type=DeviceType.unknown,
                            priority=SAVE_PRIORITY)
    else:
        dev = handle_dmidecode(info, ethernets, SAVE_PRIORITY)
    return dev


def attach_ip(dev, ip):
    """Attach the IP address"""

    ipaddr, ip_created = IPAddress.concurrent_get_or_create(address=ip)
    ipaddr.device = dev
    ipaddr.is_management = False
    ipaddr.save()


def update_shares(ssh, dev):
    """Update remote disk shares"""

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
    for ds in dev.disksharemount_set.filter(
            is_virtual=False).exclude(share__wwn__in=wwns):
        ds.delete()


def get_memory(ssh):
    """System-visible memory in MIB"""

    stdin, stdout, stderr = ssh.exec_command(
        "/bin/grep 'MemTotal:' '/proc/meminfo'")
    label, memory, unit = stdout.read().strip().split(None, 2)
    return int(int(memory) / 1024)


def get_cores(ssh):
    """System-visible core count"""

    stdin, stdout, stderr = ssh.exec_command(
        "/bin/grep '^processor' '/proc/cpuinfo'")
    return len(stdout.readlines())


def get_disk(ssh):
    """System-visible disk space in MiB"""

    stdin, stdout, stderr = ssh.exec_command(
        "/bin/df -P -x tmpfs -x devtmpfs -x ecryptfs -x iso9660 -BM "
        "| /bin/grep '^/'")
    total = 0
    for line in stdout:
        path, size, rest = line.split(None, 2)
        total += int(size.replace('M', ''))
    return total


def update_os(ssh, dev):
    """Update the OperatingSystem component."""

    stdin, stdout, stderr = ssh.exec_command("/bin/uname -a")
    family, host, version, release, rest = stdout.read().strip().split(None, 4)
    return OperatingSystem.create(
        dev=dev,
        os_name=release,
        version=version,
        family=family,
        memory=get_memory(ssh),
        storage=get_disk(ssh),
        cores_count=get_cores(ssh),
        priority=SAVE_PRIORITY
    )


def update_hostname(ssh, dev):
    """Update the hostname using a fully qualified name."""
    stdin, stdout, stderr = ssh.exec_command("/bin/hostname -f")
    dev.name = stdout.read().strip()
    dev.save(priority=SAVE_PRIORITY)


def run_ssh_linux(ssh, ip):
    ethernets = get_ethernets(ssh)
    dev = run_dmidecode(ssh, ethernets)
    if dev:
        attach_ip(dev, ip)
        update_shares(ssh, dev)
        update_os(ssh, dev)
        update_hostname(ssh, dev)
    return dev.name if dev else ''


@plugin.register(chain='discovery', requires=['ping', 'snmp'])
def ssh_linux(**kwargs):
    if 'nx-os' in kwargs.get('snmp_name', '').lower():
        return False, 'incompatible Nexus found.', kwargs
    kwargs['guessmodel'] = gvendor, gmodel = guessmodel.guessmodel(**kwargs)
    if gmodel not in {'Linux', 'ESX', 'XEN'}:
        return False, 'no match: %s %s' % (gvendor, gmodel), kwargs
    ip = str(kwargs['ip'])
    if not network.check_tcp_port(ip, 22):
        return False, 'closed.', kwargs
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
            return False, 'Authorization failed', kwargs
        name = run_ssh_linux(ssh, ip)
    except (network.Error, paramiko.SSHException) as e:
        return False, str(e), kwargs
    return True, name, kwargs
