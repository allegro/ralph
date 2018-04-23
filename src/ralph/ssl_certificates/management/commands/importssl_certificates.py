from django.core.management.base import BaseCommand
import os
from ralph.ssl_certificates.models import SSLCertificate
import datetime
import fnmatch
from cryptography.x509.extensions import ExtensionNotFound
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.x509.oid import ExtensionOID
from cryptography.x509.oid import NameOID
from ralph.assets.models.assets import AssetHolder
from pathlib import Path


class Command(BaseCommand):
    help = 'Import data to application from dir'

    def handle(self, *args, **options):
        for root, dirs, files in os.walk('/Users/maciej.skorczewski/work/sslcerts'):
            for filename in fnmatch.filter(files, '*.crt'):
                san = ''
                cert = None
                extension = None
                try:
                    pem_data = open(os.path.join(root, filename)).read()
                    cert = x509.load_pem_x509_certificate(pem_data.encode(), default_backend())
                except ValueError:
                    print('{}/{} is not valid'.format(root, filename))
                    continue

                if cert.not_valid_after < datetime.datetime.now():
                    continue
                try:
                    extension = cert.extensions.get_extension_for_oid(ExtensionOID.SUBJECT_ALTERNATIVE_NAME)
                except ExtensionNotFound:
                    pass

                if extension and extension.value:
                    san = extension.value.get_values_for_type(x509.DNSName)
                issuer = cert.issuer.get_attributes_for_oid(NameOID.ORGANIZATION_NAME)
                domain = Path(filename).stem
                issuer_name = 'CA ENT'
                asset_holder = None
                if issuer and issuer[0].value:
                    issuer_name = issuer[0].value
                asset_holder, _ = AssetHolder.objects.get_or_create(name=issuer_name)
                SSLCertificate.objects.get_or_create(
                    certificate=domain,
                    date_to=cert.not_valid_after,
                    date_from=cert.not_valid_before,
                    san=san,
                    certificate_issued_by=asset_holder
                )
