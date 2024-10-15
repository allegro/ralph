import os
from io import StringIO
from unittest.mock import MagicMock, patch

from django.core.management import call_command
from django.test import TestCase

from ralph.assets.models import Manufacturer
from ralph.ssl_certificates.models import CertificateType, SSLCertificate


class ImportSSLCertificatesTest(TestCase):
    def setUp(self):
        self.base_dir = os.path.dirname(os.path.dirname(__file__))
        self.samples_dir = os.path.join(self.base_dir, "tests", "samples")

    def test_command_output(self):
        out = StringIO()
        call_command("import_ssl_certificates", "404", stderr=out)
        self.assertIn("", out.getvalue())

    def test_wildcard_certificate_domain_ssl_should_by_without_prefix(self):  # noqa
        out = StringIO()

        call_command("import_ssl_certificates", self.samples_dir, stderr=out)
        self.assertTrue(SSLCertificate.objects.get(domain_ssl="lewitowanie.com.pl"))

    def test_ssl_should_have_proper_type(self):
        out = StringIO()
        call_command("import_ssl_certificates", self.samples_dir, stderr=out)
        self.assertTrue(
            SSLCertificate.objects.get(certificate_type=CertificateType.wildcard.id)
        )

    def test_command_should_read_issuer(self):
        out = StringIO()
        call_command("import_ssl_certificates", self.samples_dir, stderr=out)
        expected = Manufacturer.objects.get(name="My Company")
        self.assertTrue(SSLCertificate.objects.get(issued_by=expected))

    def test_command_should_read_san(self):
        out = StringIO()
        call_command("import_ssl_certificates", self.samples_dir, stderr=out)
        self.assertTrue(SSLCertificate.objects.get(san="['www.lewitowanie.com.pl']"))

    def test_certificate_domain_name(self):
        out = StringIO()
        call_command("import_ssl_certificates", self.samples_dir, stderr=out)
        self.assertTrue(SSLCertificate.objects.get(name="wildcard_lewitowanie.com.pl"))

    def test_command_rise_break_certificate(self):
        out = StringIO()
        call_command("import_ssl_certificates", self.samples_dir, stderr=out)
        self.assertIn(
            "{}/unproper/fake_ssl.crt is not valid\n".format(self.samples_dir),
            out.getvalue(),
        )


class UpdateServiceEnvTest(TestCase):
    @patch("ralph.dns.dnsaas.requests")
    @patch(
        "ralph.ssl_certificates.management.commands.update_dns_service_env_from_dnsaas.DNSaaS"
    )
    def test_command_should_informed_if_service_not_exist(
        self, dnsaas_client_class, requests
    ):
        dnsaas_client = MagicMock()
        dnsaas_client_class.side_effect = lambda: dnsaas_client
        dnsaas_client.get_api_result.return_value = [
            {
                "type": "CNAME",
                "service": {
                    "id": 1234,
                    "name": "Serwis porcelanowy",
                },
                "name": "tb-bw3.9.local",
                "content": "hhh.9.local",
            }
        ]
        requests.get.return_value = {
            "count": 1,
            "results": [
                {
                    "type": "CNAME",
                    "service": {
                        "id": 1234,
                        "name": "Serwis porcelanowy",
                    },
                    "name": "tb-bw3.9.local",
                    "content": "hhh.9.local",
                }
            ],
        }
        requests.get.return_value = MagicMock(ok=True)
        requests.get.return_value.json.return_value = requests.get.return_value
        out = StringIO()
        call_command("update_dns_service_env_from_dnsaas", stderr=out)
        self.assertIn(
            "Service with name Serwis porcelanowy and prod environment does not exist\n",
            out.getvalue(),
        )
