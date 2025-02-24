# -*- coding: utf-8 -*-
import logging
from datetime import datetime

from django.core.management.base import BaseCommand
from django.db import transaction

from ralph.security.models import SecurityScan

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Update `is_patched` field on each SecurityScan"

    @transaction.atomic
    def _update_is_patched(self):
        not_patched_ids = (
            SecurityScan.vulnerabilities.through.objects.filter(
                vulnerability__patch_deadline__lte=datetime.now()
            )
            .values_list("securityscan_id", flat=True)
            .distinct()
        )

        # this ones are outdated
        not_patched = SecurityScan.objects.filter(
            id__in=not_patched_ids,
            is_patched=True,
        ).update(is_patched=False)

        self.stdout.write("All scans: {}".format(SecurityScan.objects.count()))
        self.stdout.write("Scans marked as vulnerable: {}".format(not_patched))

    def handle(self, **options):
        self._update_is_patched()
