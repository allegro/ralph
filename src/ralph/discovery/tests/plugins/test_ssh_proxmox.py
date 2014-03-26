#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from mock import patch
from django.test import TestCase

from ralph.discovery.plugins import ssh_proxmox
from ralph.discovery.tests.util import MockSSH


def _connect_ssh_proxmox2(ip):
    return MockSSH([
        ('cat /etc/pve/cluster.cfg', ''),
        ('cat /etc/pve/cluster.conf', ''),
        ('cat /etc/pve/storage.cfg', ''),
        ('pvecm help', r"""\
USAGE: pvecm <COMMAND> [ARGS] [OPTIONS]
       pvecm help [<cmd>] [OPTIONS]

       pvecm add <hostname> [OPTIONS]
       pvecm addnode <node> [OPTIONS]
       pvecm create <clustername> [OPTIONS]
       pvecm delnode <node>
       pvecm expected <expected>
       pvecm keygen <filename>
       pvecm nodes
       pvecm status
       pvecm updatecerts  [OPTIONS]
"""),
    ])


def _connect_ssh_notproxmox(ip):
    return MockSSH([
        ('cat /etc/pve/cluster.cfg', ''),
        ('cat /etc/pve/cluster.conf', ''),
        ('cat /etc/pve/storage.cfg', ''),
        ('pvecm help', ''),
    ])


class MockMember():

    def __init__(self, *args, **kwargs):
        self.sn = 'test'


class SshProxmoxTest(TestCase):

    @patch('ralph.discovery.plugins.ssh_proxmox._connect_ssh',
           _connect_ssh_proxmox2)
    @patch('ralph.discovery.plugins.ssh_proxmox._get_master',
           MockMember)
    @patch('ralph.discovery.plugins.ssh_proxmox._add_cluster_member',
           MockMember)
    @patch('ralph.discovery.plugins.ssh_proxmox._add_virtual_machines',
           MockMember)
    def test_check_proxmox2(self):
        result = ssh_proxmox.run_ssh_proxmox('127.0.0.1')
        self.assertEqual(result, 'test')

    @patch('ralph.discovery.plugins.ssh_proxmox._connect_ssh',
           _connect_ssh_notproxmox)
    @patch('ralph.discovery.plugins.ssh_proxmox._get_master',
           MockMember)
    @patch('ralph.discovery.plugins.ssh_proxmox._add_cluster_member',
           MockMember)
    @patch('ralph.discovery.plugins.ssh_proxmox._add_virtual_machines',
           MockMember)
    def test_check_notproxmox(self):
        with self.assertRaises(ssh_proxmox.NotProxmoxError):
            ssh_proxmox.run_ssh_proxmox('127.0.0.1')
