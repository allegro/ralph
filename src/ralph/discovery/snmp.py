#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import socket

from pysnmp.entity.rfc3413.oneliner import cmdgen
from pysnmp.proto.rfc1902 import OctetString


def check_snmp_port(ip, port=161, timeout=1):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(timeout)
    try:
        s.connect((ip, port))
        s.sendall(b'0:\x02\x01\x030\x0f\x02\x02Ji\x02\x03\x00\xff\xe3\x04\x01'
                  b'\x04\x02\x01\x03\x04\x100\x0e\x04\x00\x02\x01\x00\x02\x01'
                  b'\x00\x04\x00\x04\x00\x04\x000\x12\x04\x00\x04\x00\xa0\x0c'
                  b'\x02\x027\xf0\x02\x01\x00\x02\x01\x000\x00')
        reply = s.recv(255)
    except socket.error:
        return False
    finally:
        s.close()
    return bool(reply)


def user_data(auth, snmp_version, priv_protocol=cmdgen.usmDESPrivProtocol):
    if snmp_version == '2c':
        community = auth
        data = cmdgen.CommunityData('ralph', community, 1)
    elif snmp_version in ('3', 3):
        # For snmpv3, auth is a tuple of user, password and encryption key
        snmp_v3_user, snmp_v3_auth, snmp_v3_priv = auth
        data = cmdgen.UsmUserData(
            snmp_v3_user,
            snmp_v3_auth,
            snmp_v3_priv,
            authProtocol=cmdgen.usmHMACSHAAuthProtocol,
            privProtocol=priv_protocol,
        )
    else:
        community = auth
        data = cmdgen.CommunityData('ralph', community, 0)
    return data


def snmp_command(
    hostname, community, oid, snmp_version='2c', timeout=1, attempts=3,
    priv_protocol=cmdgen.usmDESPrivProtocol
):
    transport = cmdgen.UdpTransportTarget((hostname, 161), attempts, timeout)
    data = user_data(community, snmp_version, priv_protocol=priv_protocol)
    gen = cmdgen.CommandGenerator()
    error, status, index, vars = gen.getCmd(data, transport, oid)
    if error:
        return None
    else:
        return vars


def snmp_bulk(
    hostname, community, oid, snmp_version='2c', timeout=1, attempts=3
):
    transport = cmdgen.UdpTransportTarget((hostname, 161), attempts, timeout)
    data = user_data(community, snmp_version)
    gen = cmdgen.CommandGenerator()
    if snmp_version in ('2c', '3', 3):
        error, status, index, vars = gen.bulkCmd(data, transport, 0, 25, oid)
    else:
        error, status, index, vars = gen.nextCmd(data, transport, oid)
    if error:
        return {}
    return dict(i for i, in vars)


def snmp_macs(
    hostname, community, oid, snmp_version='2c', timeout=1, attempts=3
):
    for oid, value in snmp_bulk(hostname, community, oid, snmp_version,
                                timeout, attempts).iteritems():
        if isinstance(value, OctetString):
            mac = ''.join('%02x' % ord(c) for c in value).upper()
            if len(mac) == 12:
                yield mac
