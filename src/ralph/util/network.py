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

SMBIOS_BANNER = 'ID    SIZE TYPE'

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

def smbios(as_string):
    if not as_string.startswith(SMBIOS_BANNER):
        raise ValueError("Incompatible SMBIOS answer.")
    smb = {}
    current = None
    for line in as_string.split('\n'):
        if line == SMBIOS_BANNER:
            if current:
                ctype = current['__TYPE__']
                del current['__TYPE__']
                smb.setdefault(ctype, []).append(current)
                current = None
        elif current is None:
            for token in line.split():
                if token.startswith('SMB_TYPE_'):
                    current = {'__TYPE__': token[9:]}
                    break
        else:
            if ':' in line:
                key, value = line.split(':', 1)
                current[key.strip()] = value.strip()
            else:
                current.setdefault('capabilities', []).append(line)
    return smb, as_string

def validate_ip(address):
    ip = ipaddr.IPAddress(address)
    if ip.is_unspecified or ip.is_loopback or ip.is_link_local:
        raise ValueError("Local, unspecified or loopback address: {}"
            "".format(address))
    return unicode(ip)

def normalize_wwn(wwn):
    """
    >>> normalize_wwn('50002ac2859a04c1') # 3PAR
    u'50002AC2859A04C1'
    >>> normalize_wwn('350002ac2859a04c1') # 3PAR - multipath
    u'50002AC2859A04C1'
    >>> normalize_wwn('3600508B1001030353432464243301000') # HP logical volume - multipath
    u'600508B1001030353432464243301000'
    >>> normalize_wwn('3600c0ff000d81e2cca8cbd4c01000000') # HP MSA - multipath
    u'D81E2CCA8CBD4C01'
    >>> normalize_wwn('00c0ffd81e2c0000ca8cbd4c01000000') # HP MSA
    u'D81E2CCA8CBD4C01'
    >>> normalize_wwn('3600a0b8000119ca80000574f4cfc5084') # IBM - multipath
    u'600A0B8000119CA80000574F4CFC5084'
    >>> normalize_wwn('60:0a:0b:80:00:11:9c:a8:00:00:57:4f:4c:fc:50:84') # IBM
    u'600A0B8000119CA80000574F4CFC5084'
    >>> normalize_wwn('3600144f01ef1490000004c08ed6f0008') # SUN - multipath
    u'600144F01EF1490000004C08ED6F0008'
    """

    wwn = wwn.replace(':', '').replace(' ', '').replace('.', '').strip().upper()
    if len(wwn) == 16:
        # 3PAR
        pass
    elif len(wwn) == 17:
        # 3PAR - multipath
        wwn = wwn[1:]
    elif len(wwn) == 33 and wwn[-6:] == '000000' and wwn[8:11] == '000':
        # MSA - multipath
        wwn = wwn[11:-6]
    elif len(wwn) == 32 and wwn[-6:] == '000000' and wwn[12:16] == '0000':
        # MSA
        wwn = wwn[6:12] + wwn[16:-6]
    elif len(wwn) == 32 and wwn.startswith((
            '600A0B80', # IBM
        )):
        pass
    elif len(wwn) == 33 and wwn.startswith((
            '3600A0B80', # IBM - multipath
            '3600508B1', # HP logical volume - multipath
            '3600144F0', # SUN - multipath
        )):
        wwn = wwn[1:]
    else:
        raise ValueError('Unknown WWN format %r' % wwn)
    return wwn


