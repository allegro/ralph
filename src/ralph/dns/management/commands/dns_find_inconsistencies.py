# -*- coding: utf-8 -*-
import ipaddress
import logging
from collections import defaultdict

from django.core.management.base import BaseCommand

from ralph.dns.dnsaas import DNSaaS
from ralph.networks.models import IPAddress

logger = logging.getLogger(__name__)

TEMPLATE = """
{description}

{headers}
{content}
--------------

"""


def get_ptr(ip):
    """
    Reverse `ip` to ptr.
    Example:
    >>> reverse_ip_to_ptr('192.168.1.1')
    '1.1.168.192.in-addr.arpa'
    >>> reverse_pointer('2001:db8::')
    '0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.8.b.d.0.1.0.0.2.ip6.arpa'
    """
    ip_obj = ipaddress.ip_address(ip)
    if isinstance(ip_obj, ipaddress.IPv6Address):
        reverse_chars = ip_obj.exploded[::-1].replace(":", "")
        rev_ptr = ".".join(reverse_chars) + ".ip6.arpa"
    else:
        reverse_octets = str(ip_obj).split(".")[::-1]
        rev_ptr = ".".join(reverse_octets) + ".in-addr.arpa"
    return rev_ptr


class Command(BaseCommand):
    help = "Compare DNS records in DNSaaS with state of IP-hostname in Ralph"

    # TODO (mkurek): add possibility to exclude some domains

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dns = DNSaaS()

    def _fetch_dns_records(self):
        """
        Fetch DNS Records (A and PTR) from DNSaaS.

        Returns two nested dicts, where key on the first level is record type,
        and key-values on the second level are name-content and content-name
        respectively.

        Example output:
        (
            # regular order: name -> [content]
            {
                'A': {
                    'myserver.mydc.net': ['1.2.3.4', '5.6.7.8'],
                    'myserver2.mydc.net': ['10.20.30.40']
                },
                'PTR': {
                    '4.3.2.1.in-addr.arpa': ['myserver.mydc.net'],
                    '8.7.5.6.in-addr.arpa': ['myserver.mydc.net'],
                    '40.30.20.10.in-addr.arpa': ['myserver2.mydc.net']
                }
            },
            # reversed order: content -> [name]
            {
                'A': {
                    '1.2.3.4': ['myserver.mydc.net'],
                    '5.6.7.8': ['myserver.mydc.net'],
                    '10.20.30.40': ['myserver2.mydc.net']
                },
                'PTR': {
                    'myserver.mydc.net': [
                        '4.3.2.1.in-addr.arpa', '8.7.5.6.in-addr.arpa'
                    ],
                    'myserver2.mydc.net': ['40.30.20.10.in-addr.arpa']
                }
            }
        )
        """
        url = self.dns.build_url(
            "records",
            get_params=[
                ("limit", 1000),
                ("offset", 0),
            ]
            + [("type", t) for t in {"A", "PTR"}],
        )
        api_results = self.dns.get_api_result(url)
        records_by_types = defaultdict(lambda: defaultdict(list))
        records_by_types_rev = defaultdict(lambda: defaultdict(list))
        for record in api_results:
            records_by_types[record["type"]][record["name"]].append(record["content"])
            records_by_types_rev[record["type"]][record["content"]].append(
                record["name"]
            )
        return records_by_types, records_by_types_rev

    def _get_ips(self):
        """
        Return dict with IP-hostname from Ralph.
        """
        ips = IPAddress.objects.filter(
            ethernet__base_object__cloudhost__isnull=True, hostname__isnull=False
        ).values_list("address", "hostname")
        return dict(ips)

    def get_missing_a_records_in_dnsaas(self, ips, dns, dns_rev):
        """
        Return pairs of (ip, hostname) which are present in Ralph, but not in
        DNSaaS
        """
        for ip, hostname in ips.items():
            if ip not in dns_rev["A"]:
                yield (ip, hostname)

    def get_wrong_a_records_in_dnsaas(self, ips, dns, dns_rev):
        """
        Return triplets of (ip, ralph_hostname, dns_hostname) for Records which
        are both in Ralph and DNSaaS, but are inconsistent
        """
        for ip, hostname in ips.items():
            if ip in dns_rev["A"]:
                dns_hostnames = dns_rev["A"][ip]
                if hostname not in dns_hostnames or len(dns_hostnames) != 1:
                    yield (ip, hostname, dns_hostnames)

    def get_missing_a_records_in_ralph(self, ips, dns, dns_rev):
        """
        Return pairs of (ip, list of hostnames) for Records (ips) which are
        present in DNSaaS, but they are not in Ralph.
        """
        for ip, hostnames in dns_rev["A"].items():
            if ip not in ips:
                yield (ip, hostnames)

    def check_ralph_ptrs(self, ips, dns, dns_rev):
        """
        Return pairs of (ip, hostname) which has not properly configured PTR
        records.
        """
        for ip, hostname in ips.items():
            if ip in dns_rev["A"] and hostname in dns_rev["A"][ip]:
                ptr = get_ptr(ip)
                if ptr not in dns["PTR"] or hostname not in dns["PTR"][ptr]:
                    yield (ip, hostname, dns["PTR"].get(ptr))

    def get_zombie_ptrs(self, ips, dns, dns_rev):
        """
        Return pairs of (ip, hostname) which has not properly configured PTR
        records.
        """
        for hostname, ptrs in dns_rev["PTR"].items():
            for ptr in ptrs:
                ip = ".".join(ptr.split(".")[3::-1])
                if hostname not in dns["A"] or ip not in dns["A"][hostname]:
                    yield ptr, hostname

    def get_duplicated_ptrs(self, ips, dns, dns_rev):
        """
        Return pairs of (ip, hostname) which has not properly configured PTR
        records.
        """
        for ptr, hostnames in dns["PTR"].items():
            if len(hostnames) > 1:
                yield ptr, hostnames

    def handle(self, **options):
        dns, dns_rev = self._fetch_dns_records()
        ips = self._get_ips()
        for func, headers, description in [
            (
                self.get_missing_a_records_in_dnsaas,
                ["IP", "hostname"],
                "A records missing in DNSaaS",
            ),
            (
                self.get_missing_a_records_in_ralph,
                ["IP", "hostname"],
                "A records missing in Ralph",
            ),
            (
                self.get_wrong_a_records_in_dnsaas,
                ["IP", "ralph hostname", "dnsaas hostnames"],
                "Inconsistent A records",
            ),
            (
                self.check_ralph_ptrs,
                ["IP", "ralph hostname", "PTR content"],
                "Missing or wrong PTR records",
            ),
            (self.get_zombie_ptrs, ["PTR", "hostname (content)"], "Zombie PTR records"),
            (self.get_duplicated_ptrs, ["PTR", "hostnames"], "Duplicated PTR records"),
        ]:
            result = func(ips, dns, dns_rev)
            self.stdout.write(
                TEMPLATE.format(
                    description=description,
                    headers="\t".join(headers),
                    content="\n".join(["\t".join(map(str, line)) for line in result]),
                )
            )
