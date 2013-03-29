#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import datetime
import thread

from django.conf import settings
from lck.django.common.models import MACAddressField
import MySQLdb
import sqlalchemy as sqla

from ralph.discovery.models import IPAddress, MAC_PREFIX_BLACKLIST
from ralph.util import network


PUPPET_DB_URL = settings.PUPPET_DB_URL

ENGINES = {}


def connect_db():
    thread_id = thread.get_ident()
    conn = None
    try:
        engine = ENGINES[thread_id]
        conn = engine.connect()
        _test = conn.execute("SELECT 1")
        _test.fetchall()
    except (KeyError, MySQLdb.OperationalError):
        if conn:
            conn.close()
        engine = sqla.create_engine(PUPPET_DB_URL, pool_recycle=3600)
        ENGINES[thread_id] = engine
        conn = engine.connect()
    return conn


def get_ip_hostname_sets(ip):
    hostname_set = {network.hostname(ip)}
    try:
        ip_address = IPAddress.objects.get(address=ip)
        if ip_address.device:
            ip_set = set()
            for ip in ip_address.device.ipaddress_set.all():
                ip_set.add(ip.address)
                if ip.hostname:
                    hostname_set.add(ip.hostname)
        else:
            ip_set = {ip}
    except IPAddress.DoesNotExist:
        ip_set = {ip}
    return ip_set, hostname_set


def assign_ips(dev, ip_addresses):
    ip_addresses = {str(ip) for ip in ip_addresses}
    for addr in IPAddress.objects.filter(device=dev, is_management=False):
        if addr.address in ip_addresses:
            continue
        addr.device = None
        addr.save()
    for ip in ip_addresses:
        addr, created = IPAddress.concurrent_get_or_create(address=ip)
        addr.device = dev
        addr.last_puppet = datetime.datetime.now()
        addr.save()


def get_id(arg):
    id = arg['id']
    if isinstance(id, list):
        return id[0]
    else:
        return id


def get_default_mac(facts):
    for suffix in ('', '_eth0', '_igb0', '_bnx0', '_bge0', '_nfo0', '_nge0'):
        mac = facts.get('macaddress{}'.format(suffix))
        if mac:
            result = MACAddressField.normalize(mac)
            if result[:6] in MAC_PREFIX_BLACKLIST:
                continue
            return result
    return None
