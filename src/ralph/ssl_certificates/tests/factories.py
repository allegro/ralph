# -*- coding: utf-8 -*-
from datetime import date, datetime, timedelta

import factory
from factory.django import DjangoModelFactory

from ralph.accounts.tests.factories import UserFactory
from ralph.assets.tests.factories import ManufacturerFactory
from ralph.ssl_certificates.models import CertificateType, SSLCertificate

date_now = datetime.now().date()


class SSLCertificatesFactory(DjangoModelFactory):
    name = factory.Sequence(lambda n: 'www.name{}.com'.format(n))
    certificate_type = CertificateType.ov
    business_owner = factory.SubFactory(UserFactory)
    technical_owner = factory.SubFactory(UserFactory)
    issued_by = factory.SubFactory(ManufacturerFactory)
    date_from = date_now - timedelta(days=15)
    date_to = date_now + timedelta(days=365)
    san = factory.Faker('ssn')

    class Meta:
        model = SSLCertificate
