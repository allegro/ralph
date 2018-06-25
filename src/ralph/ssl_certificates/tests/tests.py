import os
from io import StringIO
from django.core.management import call_command
from django.test import TestCase

from ralph.assets.models import Manufacturer, ServiceEnvironment
from ralph.settings import DNSAAS_URL, DNSAAS_TOKEN
from ralph.ssl_certificates.models import CertificateType, SSLCertificate


class ImportSSLCertificatesTest(TestCase):
    def setUp(self):
        self.base_dir = os.path.dirname(
            os.path.dirname(__file__)
        )

    def test_command_output(self):
        out = StringIO()
        call_command('import_ssl_certificates', '404', stderr=out)
        self.assertIn('Dir not found\n', out.getvalue())

    def test_wildcard_certificate_domain_ssl_should_by_without_prefix(self):
        out = StringIO()
        dir = os.path.join(
            self.base_dir, 'tests', 'samples'
        )
        call_command('import_ssl_certificates', dir, stderr=out)
        self.assertTrue(SSLCertificate.objects.get(domain_ssl='allegro.pl'))

    def test_ssl_should_have_proper_type(self):
        out = StringIO()
        dir = os.path.join(
            self.base_dir, 'tests', 'samples'
        )
        call_command('import_ssl_certificates', dir, stderr=out)
        self.assertTrue(SSLCertificate.objects.get(certificate_type=CertificateType.wildcard.id))

    def test_command_should_read_issuer(self):
        out = StringIO()
        dir = os.path.join(
            self.base_dir, 'tests', 'samples'
        )
        call_command('import_ssl_certificates', dir, stderr=out)
        expected = Manufacturer.objects.get(
            name='thawte, Inc.')
        self.assertTrue(SSLCertificate.objects.get(issued_by=expected))

    def test_command_should_read_san(self):
        out = StringIO()
        dir = os.path.join(
            self.base_dir, 'tests', 'samples'
        )
        call_command('import_ssl_certificates', dir, stderr=out)
        self.assertTrue(SSLCertificate.objects.get(san="['*.allegro.pl', 'allegro.pl']"))

    def test_certificate_domain_name(self):
        out = StringIO()
        dir = os.path.join(
            self.base_dir, 'tests', 'samples'
        )
        call_command('import_ssl_certificates', dir, stderr=out)
        self.assertTrue(SSLCertificate.objects.get(name='wildcard_allegro.pl'))

    def test_command_rise_break_certificate(self):
        out = StringIO()
        dir = os.path.join(
            self.base_dir, 'tests', 'samples',
        )
        call_command('import_ssl_certificates', dir, stderr=out)
        self.assertIn(
            '{}/unproper/fake_ssl.crt is not valid\n'.format(dir),
            out.getvalue()
        )

class UpdateServiceEnvTest(TestCase):
    def setUp(self):
        self.dns = DNSAAS_URL
        self.token = DNSAAS_TOKEN

    def test_command_should_informed_if_service_not_exist(self):
        out = StringIO()
        self.dns = os.environ.get('DNSAAS_URL', 'https://dnsaas.allegrogroup.com/')
        self.token = os.environ.get('DNSAAS_TOKEN', '59bbbfa312feb2fcd32300f7a47babe7c43a7d36')
        call_command('update_service_env', stderr=out)
        self.assertIn('Service with name OLX does not exist\n', out.getvalue())

    def test_command_should_update_service_env_in_cert(self):
        out = StringIO()
        call_command('update_service_env', stderr=out)
        expected = ServiceEnvironment.objects.get(
                    service__name='Ceneo', environment__name='prod'
        )
        self.assertTrue(SSLCertificate.objects.get(service_environment=expected))
