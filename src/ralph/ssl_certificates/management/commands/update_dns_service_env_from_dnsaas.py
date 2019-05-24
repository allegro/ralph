import requests
from django.conf import settings
from django.core.management.base import BaseCommand

from ralph.assets.models.assets import ServiceEnvironment
from ralph.dns.dnsaas import dnsaas_client
from ralph.ssl_certificates.models import SSLCertificate


def checking_type(value):
    # if record type is conected with mail records, then return empty string.
    # When we get empty string, management command did not change service env.
    if value['type'] in {'MX', 'TXT'}:
        domain = ''
    elif value['type'] in {'CNAME', 'PTR'}:
        domain = value['content']
    else:
        domain = value['name']
    return domain


def ssl_certificates_object_update(domain, service_env):
    SSLCertificate.objects.filter(
        domain_ssl=domain
    ).update(
        service_env=service_env
    )


class Command(BaseCommand):
    help = 'Checks the compliance of services in SSL Certificates'

    def get_records(self):
        url = dnsaas_client.build_url('records')
        response = requests.get(
            '{}'.format(url), headers={
                'Authorization': 'Token {}'.format(settings.DNSAAS_TOKEN)
            })
        limit = response.json()['count']
        record_limit = range(0, limit, 50)
        for next in record_limit:
            url = dnsaas_client.build_url('records', get_params=[
                ('limit', 50),
                ('offset', next)
            ])
            response = requests.get(
                '{}'.format(url), headers={
                    'Authorization': 'Token {}'.format(settings.DNSAAS_TOKEN)
                })
            results = response.json()['results']
            self.update_from_record(results)

    def update_from_record(self, result):
        for value in result:
            domain = checking_type(value)
            service_dns = value['service_name']
            try:
                service_env = ServiceEnvironment.objects.get(
                    service__name=service_dns, environment__name='prod'
                )
            except ServiceEnvironment.DoesNotExist:
                self.stderr.write(
                    'Service with name {} '
                    'and prod environment does not exist'.format(
                        service_dns
                    )
                )
            else:
                ssl_certificates_object_update(domain, service_env)

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
                    'Service with name {} '
                    'and prod environment does not exist'.format(
                        service_dns
                    )
                )
            else:
                ssl_certificates_object_update(domain, name)

    def get_domains(self):
        url = dnsaas_client.build_url('domains')
        return dnsaas_client.get_api_result(url)

    def handle(self, *args, **options):
        domains = self.get_domains()
        self.update_from_domains(domains)
        self.get_records()
