from io import StringIO
from django.core.management import call_command
from django.test import TestCase

class ImportSSLCertificatesTest(TestCase):
    def test_command_output(self):
        out = StringIO()
        call_command('import_ssl_certificates', '404', stderr=out)
        self.assertIn('Dir not found\n', out.getvalue())
