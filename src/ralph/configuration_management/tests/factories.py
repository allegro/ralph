from datetime import datetime

import factory
from factory.django import DjangoModelFactory

from ralph.configuration_management.models import SCMScan, SCMScanStatus


class SCMScanFactory(DjangoModelFactory):

    last_scan_date = factory.LazyFunction(datetime.now)
    scan_status = SCMScanStatus.ok

    class Meta:
        model = SCMScan
