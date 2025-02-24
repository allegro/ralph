import datetime
import fnmatch
import os
import re
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.x509.extensions import ExtensionNotFound
from cryptography.x509.oid import ExtensionOID, NameOID
from django.core.management.base import BaseCommand

from ralph.assets.models.assets import Manufacturer
from ralph.ssl_certificates.models import CertificateType, SSLCertificate

DEFAULT_ISSUER_NAME = "CA ENT"


def extract_domain_from_filename(filename):
    """
    >>> extract_domain_from_filename('wildcard_allegro.pl.crt')
    wildcard_allegro.pl
    """
    return Path(filename).stem


def get_domain_ssl(cert):
    domain_subject = cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)
    try:
        domain_ssl = domain_subject[0].value
        if domain_ssl.startswith("*."):
            domain_ssl = domain_ssl[2:]
    except IndexError:
        domain_ssl = ""
    return domain_ssl


def get_ssl_type(issuer_name, san, filename):
    ssl_type = CertificateType.ov.id
    if re.match(r"^(wildcard.+)", filename):
        ssl_type = CertificateType.wildcard.id
    elif san != "":
        ssl_type = CertificateType.multisan.id
    elif issuer_name == DEFAULT_ISSUER_NAME:
        ssl_type = CertificateType.internal.id
    return ssl_type


class Command(BaseCommand):
    help = "Import data to application from dir"

    def add_arguments(self, parser):
        parser.add_argument("certs_dir", type=str)
        parser.add_argument("repository_name", nargs="?", default="", type=str)

    def get_data_from_cert(self, cert, filename, repository_name):
        """
        get_data_from_certs takes certificate and proceed
        specific data into proper fields
        Args:
            cert - certificate
            filename - name of certificate file
        Examples:
            name=(from file name) wildcard_mysite.com,
            domain_ssl=(main domain name) mysite.com,
            certificate_type= OV,
            san=['www.mysite.com'],
            date_to=(Valid From) July 11, 2018,
            date_from=(Valid to) March 26, 2021,
            issued_by=(Issuer name) CA Company:
        """
        san = ""
        extension = None
        try:
            extension = cert.extensions.get_extension_for_oid(
                ExtensionOID.SUBJECT_ALTERNATIVE_NAME
            )
        except ExtensionNotFound:
            pass
        if extension and extension.value:
            san = extension.value.get_values_for_type(x509.DNSName)
        issuer = cert.issuer.get_attributes_for_oid(NameOID.ORGANIZATION_NAME)
        domain = extract_domain_from_filename(filename)
        issuer_name = DEFAULT_ISSUER_NAME
        if issuer and issuer[0].value:
            issuer_name = issuer[0].value
        domain_ssl = get_domain_ssl(cert)
        ssl_type = get_ssl_type(issuer_name, san, filename)
        manufacturer, _ = Manufacturer.objects.get_or_create(name=issuer_name)
        SSLCertificate.objects.get_or_create(
            name=domain,
            domain_ssl=domain_ssl,
            certificate_type=ssl_type,
            san=san,
            date_to=cert.not_valid_after,
            date_from=cert.not_valid_before,
            issued_by=manufacturer,
            certificate_repository=repository_name,
        )

    def handle(self, *args, **options):
        certs_dir = options["certs_dir"]
        repository_name = options["repository_name"]
        if not os.path.isdir(certs_dir):
            self.stdout.write(
                self.style.ERROR(
                    "Dir {} not found. Please check certs_dir option.".format(certs_dir)
                )
            )
            return
        for root, dirs, files in os.walk(certs_dir):
            for filename in fnmatch.filter(files, "*.crt"):
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
                    self.stderr.write("{}/{} is not valid\n".format(root, filename))
                    continue
                if cert.not_valid_after < datetime.datetime.now():
                    continue
                self.get_data_from_cert(cert, filename, repository_name)
