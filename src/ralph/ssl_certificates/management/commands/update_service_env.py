import sys

from django.core.management.base import BaseCommand

from ralph.assets.models.assets import ServiceEnvironment
from ralph.dns.dnsaas import dnsaas_client
from ralph.ssl_certificates.models import SSLCertificate


def checking_type(value):
    if value['type'] is 'CAME' or 'PTR':
        domain = value['content']
    else:
        domain = value['name']
    return domain


class Command(BaseCommand):
    help = 'Checks the compliance of services in SSL Certificates'

    def update_from_record(self, result):
        for value in result:
            domain = checking_type(value)
            service_dns = value['service_name']
            try:
                name = ServiceEnvironment.objects.get(
                    service__name=service_dns, environment__name='prod'
                )
            except ServiceEnvironment.DoesNotExist:
                self.stderr.write(
                    'Service with name {} does not exist'.format(service_dns)
                )
            else:
                SSLCertificate.objects.filter(
                    domain_ssl=domain).update(
                    service_env=name)

    def update_from_domains(self, result):
        for value in result:
            domain = value['name']
            service_dns = value['service_name']
            try:
                name = ServiceEnvironment.objects.get(
                    service__name=service_dns, environment__name='prod'
                )
            except ServiceEnvironment.DoesNotExist:
                self.stderr.write(
                    'Service with name {} does not exist'.format(service_dns)
                )
            else:
                SSLCertificate.objects.filter(
                    domain_ssl=domain).update(
                    service_env=name)

    def get_records(self):
        url = dnsaas_client.build_url('records')
        return dnsaas_client.get_api_result(url)

    def get_domains(self):
        url = dnsaas_client.build_url('domains')
        return dnsaas_client.get_api_result(url)

    def handle(self, *args, **options):
        sys.setrecursionlimit(1500)
        domains = self.get_domains()
        self.update_from_domains(domains)
        records = self.get_records()
        self.update_from_record(records)
