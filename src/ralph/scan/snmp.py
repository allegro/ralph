# -*- coding: utf-8 -*-

"""
Set of usefull functions to retrieve data from SNMP.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.conf import settings
from pysnmp.entity.rfc3413.oneliner import cmdgen

from ralph.discovery.snmp import snmp_command, check_snmp_port


SNMP_COMMUNITIES = getattr(settings, 'SNMP_PLUGIN_COMMUNITIES', ['public'])
SNMP_V3_AUTH = (
    settings.SNMP_V3_USER,
    settings.SNMP_V3_AUTH_KEY,
    settings.SNMP_V3_PRIV_KEY,
)
if not all(SNMP_V3_AUTH):
    SNMP_V3_AUTH = None
PRIV_PROTOCOLS = (
    cmdgen.usmDESPrivProtocol,
    cmdgen.usmAesCfb128Protocol,
    cmdgen.usmAesCfb192Protocol,
    cmdgen.usmAesCfb256Protocol,
)


def _snmp(
    ip, community, oid, attempts=2, timeout=3, snmp_version='2c',
    priv_protocol=cmdgen.usmDESPrivProtocol
):
    result = snmp_command(
        str(ip), community, oid, attempts=attempts, timeout=timeout,
        snmp_version=snmp_version, priv_protocol=priv_protocol,
    )
    if result is None:
        message = None
    else:
        message = unicode(result[0][1])
    return message


def get_snmp(ipaddress):
    community = ipaddress.snmp_community
    version = ipaddress.snmp_version or '2c'
    oid = (1, 3, 6, 1, 2, 1, 1, 1, 0)  # sysDesc
    http_family = ipaddress.http_family
    message = None
    # Windows hosts always say that the port is closed, even when it's open
    if http_family not in ('Microsoft-IIS', 'Unspecified', 'RomPager'):
        if not check_snmp_port(ipaddress.address):
            return None, None, None
    if http_family == 'HP':
        version = '1'
        oid = (1, 3, 6, 1, 4, 1, 2, 3, 51, 2, 2, 21, 1, 1, 5, 0)
        # bladeCenterManufacturingId
    if http_family == 'RomPager':
        version = '1'
    if version != '3':
        # Don't try SNMP v2 if v3 worked on this host.
        communities = list(SNMP_COMMUNITIES)
        if community:
            if community in communities:
                communities.remove(community)
            communities.insert(0, community)
        for community in communities:
            message = _snmp(
                ipaddress.address,
                community,
                oid,
                attempts=2,
                timeout=0.2,
                snmp_version=version,
            )
            if message == '' and version != '1':
                # prevent empty response for some communities.
                version = '1'
                message = _snmp(
                    ipaddress.address,
                    community,
                    oid,
                    attempts=2,
                    timeout=0.2,
                    snmp_version=version,
                )
            if message:
                return message, community, version
    if SNMP_V3_AUTH:
        version = '3'
        for priv_protocol in PRIV_PROTOCOLS:
            message = _snmp(
                ipaddress.address,
                SNMP_V3_AUTH,
                oid,
                attempts=2,
                timeout=2,  # SNMP v3 usually needs more time
                snmp_version=version,
                priv_protocol=priv_protocol,
            )
            if message:
                return message, community, version
    if not message:
        return None, None, None
    return message, community, version
