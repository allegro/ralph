import datetime
import fnmatch
import os
import re
import sys
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.x509.extensions import ExtensionNotFound
from cryptography.x509.oid import ExtensionOID, NameOID
from django.core.management.base import BaseCommand

from ralph.assets.models.assets import Manufacturer
from ralph.ssl_certificates.models import CertificateType, SSLCertificate


def extract_domain_from_filename(filename):
    """
    >>> extract_domain_from_filename('wildcard_allegro.pl.crt')
    wildcard_allegro.pl
    """
    return Path(filename).stem


def get_domain_ssl(cert):
    domain_subject = cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)
    domain_ssl = domain_subject[0].value
    if domain_ssl.startswith('*.'):
        domain_ssl = domain_ssl[2:]
    return domain_ssl

def get_ssl_type(issuer_name, san, filename):
    type_ssl = CertificateType.ov.id
    if re.match(r'^(wildcard.+)', filename):
        type_ssl = CertificateType.wildcard.id
    elif san is not '':
        type_ssl = CertificateType.multisan.id
    elif issuer_name == 'CA ENT':
        type_ssl = CertificateType.internal.id
    return type_ssl

class Command(BaseCommand, ):
    help = 'Import data to application from dir'

    def add_arguments(self, parser):
        parser.add_argument('certs_dir', type=str)

    def get_san(self, cert):
        san = ''
        extension = None
        try:
            extension = cert.extensions.get_extension_for_oid(ExtensionOID.SUBJECT_ALTERNATIVE_NAME)
        except ExtensionNotFound:
            pass
        if extension and extension.value:
            san = extension.value.get_values_for_type(x509.DNSName)
        return san

    def ssl_values(self, cert, san, filename):
        issuer = cert.issuer.get_attributes_for_oid(
            NameOID.ORGANIZATION_NAME
        )
        domain = extract_domain_from_filename(filename)
        issuer_name = 'CA ENT'
        if issuer and issuer[0].value:
            issuer_name = issuer[0].value
        domain_ssl = get_domain_ssl(cert)
        type_ssl = get_ssl_type(issuer_name, san, filename)
        manufacturer, _ = Manufacturer.objects.get_or_create(
            name=issuer_name
        )
        SSLCertificate.objects.get_or_create(
            name=domain,
            domain_ssl=domain_ssl,
            certificate_type=type_ssl,
            san=san,
            date_to=cert.not_valid_after,
            date_from=cert.not_valid_before,
            issued_by=manufacturer
        )

    def handle(self, *args, **options):
        self.stderr.write('Dir not found')
        certs_dir = options['certs_dir']
        for root, dirs, files in os.walk(certs_dir):
            for filename in fnmatch.filter(files, '*.crt'):
                cert = None
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
                san = self.get_san(cert)
                self.ssl_values(cert, san, filename)
