from datetime import datetime, timedelta

import factory
from factory.django import DjangoModelFactory

from ralph.assets.tests.factories import (
    ManufacturerFactory,
    ServiceEnvironmentFactory
)
from ralph.ssl_certificates.models import CertificateType, SSLCertificate

date_now = datetime.now().date()


class SSLCertificatesFactory(DjangoModelFactory):
    name = factory.Sequence(lambda n: "www.name{}.com".format(n))
    certificate_type = CertificateType.ov
    issued_by = factory.SubFactory(ManufacturerFactory)
    date_from = date_now - timedelta(days=15)
    date_to = date_now + timedelta(days=365)
    san = factory.Faker("ssn")
    service_env = factory.SubFactory(ServiceEnvironmentFactory)

    class Meta:
        model = SSLCertificate
