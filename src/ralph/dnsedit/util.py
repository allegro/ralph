# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import re

import ralph.discovery.models_device as discovery_models

from django.db import models as db
from lck.django.common import nested_commit_on_success
from lck.django.common.models import MACAddressField
from powerdns.models import Domain, Record

from ralph.dnsedit.models import DHCPEntry


HOSTNAME_CHUNK_PATTERN = re.compile(
    r'^([A-Z\d][A-Z\d-]{0,61}[A-Z\d]|[A-Z\d])$',
    re.IGNORECASE,
)


class Error(Exception):
    pass


class RevDNSExists(Error):

    """Trying to create a Reverse DNS record for IP that already has one."""


class RevDNSNoDomain(Error):

    """
    Trying to create a Reverse DNS record for IP that has no in-addr-arpa.
    """


def is_valid_hostname(hostname):
    """Check if a hostname is valid"""
    if len(hostname) > 255:
        return False
    hostname = hostname.rstrip('.')
    return all(HOSTNAME_CHUNK_PATTERN.match(x) for x in hostname.split("."))


def clean_dns_name(name):
    """Remove all entries for the specified name from the DNS."""
    name = name.strip().strip('.')
    for r in Record.objects.filter(name=name):
        r.delete()


def clean_dns_address(ip):
    """Remove all A entries for the specified IP address from the DNS."""
    ip = str(ip).strip().strip('.')
    for r in Record.objects.filter(content=ip, type='A'):
        r.delete()


def clean_dns_entries(ip):
    """Remove all entries for the specified IP address from the DNS,
    including PTR entries.
    May leave behind some CNAME entries pointing to that IP address.
    """
    ip = str(ip).strip().strip('.')
    for r in Record.objects.filter(content=ip):
        r.delete()
    for rev in get_revdns_records(ip):
        rev.delete()


def add_dns_address(name, ip):
    """Add a new DNS record in the right domain."""
    name = name.strip().strip('.')
    ip = str(ip).strip().strip('.')
    host_name, domain_name = name.split('.', 1)
    domain = Domain.objects.get(name=domain_name)
    Record.objects.get_or_create(
        domain=domain,
        name=name,
        type='A',
        content=ip,
    )


@nested_commit_on_success
def reset_dns(name, ip):
    """Make sure the name is the only one pointing to specified IP."""
    clean_dns_name(name)
    clean_dns_address(ip)
    add_dns_address(name, ip)
    set_revdns_record(ip, name, create=True, overwrite=True)


def clean_dhcp_mac(mac):
    """Remove all DHCP entries for the given MAC."""
    mac = MACAddressField.normalize(mac)
    for e in DHCPEntry.objects.filter(mac=mac):
        e.delete()


def clean_dhcp_ip(ip):
    """Remove all DHCP entries for the given IP."""
    ip = str(ip).strip().strip('.')
    for e in DHCPEntry.objects.filter(ip=ip):
        e.delete()


def reset_dhcp(ip, mac):
    mac = MACAddressField.normalize(mac)
    ip = str(ip).strip().strip('.')
    entry = DHCPEntry(ip=ip, mac=mac)
    entry.save()


def get_domain(name):
    parts = name.split('.')
    superdomains = [".".join(parts[i:]) for i in xrange(len(parts))]
    domains = Domain.objects.filter(name__in=superdomains).extra(
        select={'length': 'Length(name)'},
    ).order_by('-length', 'name')
    for domain in domains:
        return domain


def get_revdns_records(ip):
    revname = '.'.join(reversed(ip.split('.'))) + '.in-addr.arpa'
    return Record.objects.filter(name=revname, type='PTR')


def find_addresses_for_hostname(hostname):
    rev_ips = {
        '.'.join(reversed(name.split('.', 4)[:4]))
        for name in Record.objects.filter(
            type='PTR',
            content=hostname,
        ).values_list(
            'name',
            flat=True,
        )
    }
    ips = set(
        Record.objects.filter(
            type='A',
            name=hostname,
        ).values_list(
            'content',
            flat=True,
        )
    )
    return ips | rev_ips


@nested_commit_on_success
def set_revdns_record(ip, name, ttl=None, prio=None, overwrite=False,
                      create=False):
    revname = '.'.join(reversed(ip.split('.'))) + '.in-addr.arpa'
    domain_name = '.'.join(list(reversed(ip.split('.')))[1:]) + '.in-addr.arpa'
    if not create:
        try:
            domain = Domain.objects.get(name=domain_name)
        except Domain.DoesNotExist:
            raise RevDNSNoDomain('Domain %s not found.' %
                                 domain_name)
    else:
        domain, created = Domain.objects.get_or_create(name=domain_name)
    records = Record.objects.filter(name=revname, type='PTR')
    creating = True
    for record in records:
        creating = False
        if not overwrite and record.content != name:
            raise RevDNSExists('RevDNS record for %s already exists.' %
                               revname)
    if creating:
        records = [Record(name=revname, type='PTR')]
    for record in records:
        record.content = name
        record.domain = domain
        if ttl is not None:
            record.ttl = ttl
        if prio is not None:
            record.prio = prio
        record.save()
    return create


@nested_commit_on_success
def set_txt_record(domain, name, title, value):
    """Updates or creates a TXT record with the given title."""
    try:
        record = Record.objects.get(
            type='TXT',
            name=name,
            domain=domain,
            content__startswith=title + ': ',
        )
    except Record.DoesNotExist:
        record = Record(name=name, type='TXT', domain=domain)
    record.content = '%s: %s' % (title, value)
    record.save()


def get_location(device):
    location = []
    node = device
    while node:
        position = node.get_position() or ''
        if position:
            position = ' [%s]' % position
        location.append(node.name + position)
        node = node.parent
    return " / ".join(reversed(location))


def get_model(device):
    if not device.model:
        return ''
    model = '[%s] %s' % (
        discovery_models.DeviceType.name_from_id(device.model.type),
        device.model.name
    )
    if device.model.group:
        model += ' {%s}' % device.model.group.name
    return model


@nested_commit_on_success
def update_txt_records(device):
    """Update the TXT records for the given device."""
    hostnames = set()
    addresses = set()
    for ipaddress in device.ipaddress_set.all():
        if ipaddress.hostname:
            hostnames.add(ipaddress.hostname)
        addresses.add(ipaddress.address)
    record_names = set()
    for record in Record.objects.filter(
        db.Q(name__in=hostnames) | db.Q(content__in=addresses),
        type='A',
    ):
        if get_revdns_records(record.content).filter(
            content=record.name,
        ).exists():
            # Only update those host names, that have both A and PTR records.
            record_names.add(record.name)
    for name in record_names:
        set_txt_record(
            record.domain,
            name,
            'VENTURE',
            device.venture.name if device.venture else ''
        )
        set_txt_record(
            record.domain,
            name,
            'ROLE',
            device.venture_role.full_name if device.venture_role else ''
        )
        set_txt_record(record.domain, name, 'MODEL', get_model(device))
        set_txt_record(record.domain, name, 'LOCATION', get_location(device))
