from datetime import datetime

import factory
from factory.django import DjangoModelFactory

from ralph.configuration_management.models import SCMCheckResult, SCMStatusCheck


class SCMStatusCheckFactory(DjangoModelFactory):
    last_checked = factory.LazyFunction(datetime.now)
    check_result = SCMCheckResult.scm_ok

    class Meta:
        model = SCMStatusCheck
