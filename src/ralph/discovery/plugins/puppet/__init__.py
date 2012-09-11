#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Discovery configuration."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import datetime
import random
import re
import time

from lck.django.common import nested_commit_on_success
import MySQLdb
from django.conf import settings

from ralph.util import network, plugin
from ralph.discovery.models import IPAddress, DiskShare, DiskShareMount
from ralph.discovery import hardware

from .facts import parse_facts, handle_facts_os
from .lshw import parse_lshw
from .util import connect_db, get_ip_hostname_sets


SAVE_PRIORITY = 51


@plugin.register(chain='discovery', requires=['ping'], priority=200)
def puppet(**kwargs):
    if not settings.PUPPET_DB_URL:
        return False, "not configured", kwargs
    ip = str(kwargs['ip'])
    ip_set, hostname_set = get_ip_hostname_sets(ip)
    db = connect_db()
    facts = get_all_facts_by_ip_set(db, ip_set)
    if not facts and hostname_set:
        facts = get_all_facts_by_hostname_set(db, hostname_set)
    if not facts:
        return False, "host config not found.", kwargs

    try:
        is_virtual = is_host_virtual(facts)
        try:
            lshw = facts['lshw']
        except KeyError:
            dev, dev_name = parse_facts(facts, is_virtual)
        else:
            dev, dev_name = parse_lshw(lshw, facts, is_virtual)
    except MySQLdb.OperationalError as e:
        if e.args[0] in (1205, 1213) and 'try restarting transaction' in e.args[1]:
            time.sleep(random.choice(range(10)) + 1)
            raise plugin.Restart(unicode(e), kwargs)
        raise
    if not dev:
        return False, dev_name, kwargs

    parse_wwn(facts, dev)
    parse_smartctl(facts, dev)
    parse_hpacu(facts, dev)
    parse_megaraid(facts, dev)
    parse_uptime(facts, dev)

    ip_address, created = IPAddress.concurrent_get_or_create(address=str(ip))
    ip_address.device, message = dev, dev_name
    if created:
        ip_address.hostname = network.hostname(ip_address.address)
    ip_address.last_puppet = datetime.datetime.now()
    ip_address.save(update_last_seen=True) # no priorities for IP addresses

    handle_facts_os(dev, facts, is_virtual)

    return True, message, kwargs

def get_all_facts_by_ip_set(db, ip_set):
    facts = None
    for ip in ip_set:
        rows = db.execute("""SELECT fn.name, fv.value
                            FROM hosts h, fact_values fv, fact_names fn
                            WHERE h.ip=%s AND fv.host_id=h.id
                            AND fv.fact_name_id=fn.id""", ip)
        _facts = dict(rows.fetchall())
        if _facts:
            if _facts['virtual'] == 'zone':
                continue
            if not facts:
                facts = _facts
            else:
                raise ValueError("more than 1 machine reported by Puppet for "
                    "this IP set: {}".format(ip_set))
    return facts

def get_all_facts_by_hostname_set(db, hostname_set):
    facts = None
    for hostname in hostname_set:
        rows = db.execute("""SELECT fn.name, fv.value
                            FROM hosts h, fact_values fv, fact_names fn
                            WHERE h.name=%s AND fv.host_id=h.id
                            AND fv.fact_name_id=fn.id""", hostname)
        _facts = dict(rows.fetchall())
        if _facts:
            if not facts:
                facts = _facts
            else:
                raise ValueError("more than 1 machine reported by Puppet for "
                    "this hostname set: {}".format(hostname_set))
    return facts

def is_host_virtual(facts):
    is_virtual = facts.get('virtual', 'physical') not in ('physical',
        'openvz', 'openvzhn')
    if facts.get('manufacturer') == 'Bochs' and not is_virtual:
        facts['virtual'] = 'virtual'
        is_virtual = True
    return is_virtual

@nested_commit_on_success
def parse_wwn(facts, dev):
    def make_mount(wwn):
        try:
            share = DiskShare.objects.get(wwn=wwn)
        except DiskShare.DoesNotExist:
            return None
        mount, created = DiskShareMount.concurrent_get_or_create(
                share=share, device=dev)
        return mount
    wwns = []
    for key, wwn in facts.iteritems():
        if not key.startswith('wwn_mpath'):
            continue
        wwns.append(hardware.normalize_wwn(wwn))
    for wwn in wwns:
        mount = make_mount(wwn)
        if not mount:
            continue
        path = key.replace('wwn_', '')
        mount.volume = '/dev/mapper/%s' % path
        mount.save(priority=SAVE_PRIORITY)
    for mount in dev.disksharemount_set.filter(
            server=None).exclude(share__wwn__in=wwns):
        mount.delete()


HPACU_GENERAL_REGEX = re.compile(r'hpacu_([^_]+)__(.+)')
HPACU_LOGICAL_PHYSICAL_REGEX = re.compile(r'([^_]+)__(.+)')

@nested_commit_on_success
def parse_hpacu(facts, dev):
    disks = {}
    for k, value in facts.iteritems():
        m = HPACU_GENERAL_REGEX.match(k)
        if not m:
            continue
        n = HPACU_LOGICAL_PHYSICAL_REGEX.match(m.group(2))
        physical_disk = n.group(1) if n else None
        property = n.group(2) if n else m.group(2)
        if not physical_disk:
            continue
        disks.setdefault(physical_disk, {})[property] = value.strip()
    hardware.handle_hpacu(dev, disks, SAVE_PRIORITY)

SMARTCTL_REGEX = re.compile(r'smartctl_([^_]+)__(.+)')

@nested_commit_on_success
def parse_smartctl(facts, dev):
    disks = {}
    for k, value in facts.iteritems():
        m = SMARTCTL_REGEX.match(k)
        if not m:
            continue
        disk = m.group(1)
        property = m.group(2)
        disks.setdefault(disk, {})[property] = value.strip()
    hardware.handle_smartctl(dev, disks, SAVE_PRIORITY)

MEGARAID_REGEX = re.compile(r'megacli_([^_]+)_([^_]+)__(.+)')

@nested_commit_on_success
def parse_megaraid(facts, dev):
    disks = {}
    for k, value in facts.iteritems():
        m = MEGARAID_REGEX.match(k)
        if not m:
            continue

        controller = m.group(1)
        disk = m.group(2)
        property = m.group(3)
        disks.setdefault((controller, disk), {})[property] = value.strip()
    hardware.handle_megaraid(dev, disks, SAVE_PRIORITY)

@nested_commit_on_success
def parse_uptime(facts, dev):
    try:
        uptime = int(facts['uptime_seconds'])
    except (KeyError, TypeError, ValueError):
        uptime = None
    dev.uptime = uptime
    dev.save()
