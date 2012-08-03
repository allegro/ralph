#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Low-level network utilities, silently returning empty answers in place of
domain-related exceptions."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import socket
import sys
import StringIO

from dns.exception import DNSException
from lck.cache import memoize
import dns.resolver
import ipaddr
import ssh as paramiko
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
        except DNSException: # dns.resolver.NXDOMAIN, dns.resolver.NoAnswer
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


def connect_ssh(ip, username, password=None, client=paramiko.SSHClient, key=None):
    ssh = client()
    ssh.set_log_channel('critical_only')
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    if key:
        f = StringIO.StringIO(key)
        pkey = paramiko.DSSKey(file_obj=f)
    else:
        pkey = None
    try:
        ssh.connect(ip, username=username, password=password, pkey=pkey)
    except (paramiko.AuthenticationException, EOFError) as e:
        raise AuthError(str(e))
    return ssh


def validate_ip(address):
    ip = ipaddr.IPAddress(address)
    if ip.is_unspecified or ip.is_loopback or ip.is_link_local:
        raise ValueError("Local, unspecified or loopback address: {}"
            "".format(address))
    return unicode(ip)
