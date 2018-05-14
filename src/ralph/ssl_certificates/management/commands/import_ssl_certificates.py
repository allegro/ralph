import datetime
import fnmatch
import os
import sys
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.x509.extensions import ExtensionNotFound
from cryptography.x509.oid import ExtensionOID, NameOID
from django.core.management.base import BaseCommand

from ralph.assets.models.assets import AssetHolder
from ralph.ssl_certificates.models import SSLCertificate


class Command(BaseCommand):

    help = 'Import data to application from dir'

    def add_arguments(self, parser):
        parser.add_argument('certs_dir', type=str)

    def handle(self, *args, **options):
        certs_dir = options['certs_dir']
        for root, dirs, files in os.walk(certs_dir):
            for filename in fnmatch.filter(files, '*.crt'):
                san = ''
                cert = None
                extension = None
                pem_data = None
                try:
                    with open(os.path.join(root, filename)) as f:
                        pem_data = f.read()
                except IOError:
                    continue
                try:
                    cert = x509.load_pem_x509_certificate(
                        pem_data.encode(), default_backend()
                    )
                except ValueError:
                    sys.stderr.write(
                        '{}/{} is not valid\n'.format(root, filename)
                    )
                    continue

                if cert.not_valid_after < datetime.datetime.now():
                    continue
                try:
                    extension = cert.extensions.get_extension_for_oid(
                        ExtensionOID.SUBJECT_ALTERNATIVE_NAME
                    )
                except ExtensionNotFound:
                    pass

                if extension and extension.value:
                    san = extension.value.get_values_for_type(x509.DNSName)
                issuer = cert.issuer.get_attributes_for_oid(
                    NameOID.ORGANIZATION_NAME
                )
                domain = Path(filename).stem
                issuer_name = 'CA ENT'
                if issuer and issuer[0].value:
                    issuer_name = issuer[0].value
                asset_holder, _ = AssetHolder.objects.get_or_create(
                    name=issuer_name
                )
                SSLCertificate.objects.get_or_create(
                    name=domain,
                    date_to=cert.not_valid_after,
                    date_from=cert.not_valid_before,
                    san=san,
                    issued_by=asset_holder
                )
