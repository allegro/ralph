# -*- coding: utf-8 -*-
from datetime import datetime

import factory
from factory.django import DjangoModelFactory

# from ralph.accounts.tests.factories import RegionFactory
from ralph.assets.tests.factories import BaseObjectFactory
from ralph.security.choices import Risk, ScanStatus
from ralph.security.models import SecurityScan, Vulnerability


class SecurityScanFactory(DjangoModelFactory):

    class Meta:
        model = SecurityScan

    last_scan_date = datetime(2015, 1, 1)
    scan_status = ScanStatus.ok
    next_scan_date = datetime(2016, 1, 1)
    details_url = 'https://www.example.com/details'
    rescan_url = 'https://www.example.com/rescan'
    asset = factory.SubFactory(BaseObjectFactory)


class VulnerabilityFactory(DjangoModelFactory):

    name = factory.Sequence(lambda n: 'vulnserability %d' % n)
    days_to_patch = 10
    risk = Risk.low
    external_vulnerability_id = factory.Sequence(lambda n: n)
    security_scan = factory.SubFactory(SecurityScanFactory)

    class Meta:
        model = Vulnerability
