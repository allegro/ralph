# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from powerdns.models import Domain, Record
from lck.django.common import nested_commit_on_success


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

def add_dns_address(name, ip):
    """Add a new DNS record in the right domain."""
    name = name.strip().strip('.')
    ip = str(ip).strip().strip('.')
    host_name, domain_name = name.split('.', 1)
    domain = Domain.objects.get(name=domain_name)
    record = Record(
        domain=domain,
        name=name,
        type='A',
        content=ip,
    )
    record.save()

@nested_commit_on_success
def reset_dns(name, ip):
    """Make sure the name is the only one pointing to specified IP."""
    clean_dns_name(name)
    clean_dns_address(ip)
    add_dns_address(name, ip)

