# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.conf import settings

from ralph.scan.plugins import get_base_result_template
from ralph.util import network


SETTINGS = settings.SCAN_PLUGINS.get(__name__, {})


class Error(Exception):
    pass


class ConnectionError(Error):
    pass


class NotProxmoxError(Error):
    pass


def _connect_ssh(ip_address, user, password):
    if not network.check_tcp_port(ip_address, 22):
        raise ConnectionError('Port 22 closed on a Proxmox server.')
    return network.connect_ssh(ip_address, user, password)


def _get_master(ssh, ip_address):
    stdin, stdout, stderr = ssh.exec_command("cat /etc/pve/cluster.cfg")
    data = stdout.read()
    if not data:
        stdin, stdout, stderr = ssh.exec_command("pvesh get /nodes")
        data = stdout.read()


def _ssh_proxmox(ip_address, user, password):
    ssh = _connect_ssh(ip_address, user, password)
    try:
        for command in (
            'cat /etc/pve/cluster.cfg',
            'cat /etc/pve/cluster.conf',
            'cat /etc/pve/storage.cfg',
            'pvecm help',
        ):
            stdin, stdout, stderr = ssh.exec_command(command)
            data = stdout.read()
            if data != '':
                break
        else:
            raise NotProxmoxError('This is not a PROXMOX server.')
        device_info = _get_master(ssh, ip_address)
    finally:
        ssh.close()
    return device_info


def scan_address(ip_address, **kwargs):
    user = SETTINGS.get('user')
    password = SETTINGS.get('password')
    messages = []
    result = get_base_result_template('ssh_proxmox', messages)
    if not user or not password:
        result['status'] = 'error'
        messages.append(
            'Not configured. Set SSH_USER and SSH_PASSWORD in your '
            'configuration file.',
        )
    else:
        try:
            device_info = _ssh_proxmox(ip_address, user, password)
        except (ConnectionError, NotProxmoxError) as e:
            result['status'] = 'error'
            messages.append(unicode(e))
        else:
            result.update({
                'status': 'success',
                'device': device_info,
            })
    return result

