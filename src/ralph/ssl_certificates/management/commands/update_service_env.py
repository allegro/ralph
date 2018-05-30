from django.core.management.base import BaseCommand

from ralph.assets.models.assets import ServiceEnvironment
from ralph.dns.dnsaas import dnsaas_client
from ralph.ssl_certificates.models import SSLCertificate

Command().UPDATE(RESULTS=[{}])
class Command(BaseCommand):
    help = 'Checks the compliance of services in SSL Certificates'

    def update_from_record(self, results):
        for value in results:
            domain = value['content']
            service_dns = value['service_uid']
            uid = None
            try:
                uid = ServiceEnvironment.objects.get(service__uid=service_dns)
            except ServiceEnvironment.DoesNotExist:
                self.stderr.write('Service with uid {} does not exist'.format(service_dns))
            SSLCertificate.objects.filter(domain_ssl=domain).update(service_environment=uid)

    def update_from_domains(self, results):
        for value in results:
            domain = value['name']
            service_dns = value['service_name']
            name = None
            try:
                name = ServiceEnvironment.objects.get(service__name=service_dns, environment__name='prod')
            except ServiceEnvironment.DoesNotExist:
                self.stderr.write('Service with name {} does not exist'.format(service_dns))
            SSLCertificate.objects.filter(domain_ssl=domain).update(service_environment=name)

    def get_records(self):
        url = dnsaas_client.build_url('records')
        return dnsaas_client.get_api_result(url)

    def get_domains(self):
        url = dnsaas_client.build_url('domains')
        return dnsaas_client.get_api_result(url)

    def handle(self, *args, **options):
        records = self.get_records()
        self.update_from_record(records)
        domains = self.get_domains()
        self.update_from_domains(domains)

