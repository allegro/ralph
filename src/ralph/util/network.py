#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Low-level network utilities, silently returning empty answers in place of
domain-related exceptions."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging
import socket
import StringIO
import sys
import time

from dns.exception import DNSException
from lck.cache import memoize
import dns.resolver
import ipaddr
import paramiko
from ping import do_one


class Error(Exception):
    pass


class ConnectError(Error):
    pass


class AuthError(Error):
    pass


@memoize
def hostname(ip, reverse=False):
    """hostname(ip) -> 'hostname'

    `ip` may be a string or ipaddr.IPAddress instance.
    If no hostname known, returns None."""
    try:
        result = socket.gethostbyaddr(str(ip))
        return result[0] if not reverse else result[2][0]
    except socket.error:
        return None


def descriptions(host):
    """descriptions(host) -> ['descriptive text 1', 'descriptive text 2', ...]

    Lists DNS descriptive text for the specified `host`. `host` may be a string
    holding a hostname or IP, or ipaddr.IPAddress instance. If no descriptions
    are known, the returned list is empty."""
    host = hostname(str(host))
    result = []
    if host:
        try:
            for answer in dns.resolver.query(host, 'TXT'):
                result.append(str(answer).strip('"'))
        except DNSException:  # dns.resolver.NXDOMAIN, dns.resolver.NoAnswer
            pass
    return result


def ping(hostname, timeout=0.2, attempts=2, packet_size=64):
    """ping(hostname, [timeout, attempts, packet_size]) -> float

    Returns the ping value to a specified `hostname`. Possible customizations:
    `timeout`, `attempts` and `packet_size`."""
    for i in xrange(attempts):
        try:
            result = do_one(str(hostname), timeout, packet_size)
            if result is not None:
                break
        except socket.error:
            result = None
    return result


def ping_main(hostname=None, timeout=0.2, attempts=2):
    """ping as a command. Installed as pping by setuptools."""
    # FIXME: This needs proper argparse support.
    if not hostname and len(sys.argv) != 2:
        sys.stderr.write("error: one command-line argument (host) expected.")
        sys.exit(15)
    hostname = sys.argv[1]
    sys.exit(0 if bool(ping(hostname, timeout, attempts)) else 1)


def check_tcp_port(ip, port, timeout=1):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    result = s.connect_ex((ip, port))
    s.close()
    return result == 0


def connect_ssh(
    ip, username, password=None, client=paramiko.SSHClient,
    key=None, timeout=15.0,
):
    ssh = client()
    ssh.set_log_channel('critical_only')
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    if key:
        f = StringIO.StringIO(key)
        pkey = paramiko.DSSKey(file_obj=f)
    else:
        pkey = None
    try:
        ssh.connect(
            ip, username=username, password=password, pkey=pkey,
            timeout=timeout,
        )
    except (paramiko.AuthenticationException, EOFError) as e:
        raise AuthError(str(e))
    return ssh


class CiscoSSHHandler(object):

    def __init__(self, ip, username=None, password=None):
        self.ip = ip
        self.username = username
        self.password = password

        # setup logging
        self.logger = logging.getLogger(__name__)
        self.logger.info("Using username: {}".format(self.username))

        # setup paramiko
        self.ssh = paramiko.SSHClient()
        self.ssh.load_system_host_keys()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    def connect(self):
        self.ssh.connect(
            self.ip, username=self.username, password=self.password,
            allow_agent=False,
        )
        self.channel = self.ssh.invoke_shell()

        # disables output scrolling
        self.channel.send("terminal length 0\n")

        time.sleep(1)
        self.output = self.channel.recv(9999)
        self.channel.send("\n")

    def cisco_command(self, command):
        self.logger.info("Running command: {}".format(command))
        self.channel.send(command + "\n")
        time.sleep(2)
        buff = ['']
        while True:
            lines = self.channel.recv(9999).split("\n")
            buff[-1] += lines[0]
            buff.extend(lines[1:])
            if buff[-1].endswith(('#', '>')):
                return buff[1:-1]

    def close(self):
        self.logger.info("Close connection.")
        self.ssh.close()


def connect_cisco_ssh(ip, username, password):
    ssh = CiscoSSHHandler(ip, username, password)
    try:
        ssh.connect()
    except (paramiko.AuthenticationException, EOFError) as e:
        raise AuthError(str(e))
    return ssh


def validate_ip(address):
    ip = ipaddr.IPAddress(address)
    if ip.is_unspecified or ip.is_loopback or ip.is_link_local:
        raise ValueError("Local, unspecified or loopback address: {}"
                         "".format(address))
    return unicode(ip)
