# -*- coding: utf-8 -*-
import logging
from datetime import datetime

from django.core.management.base import BaseCommand

from ralph.security.models import SecurityScan


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Update `is_patched` field on each SecurityScan'

    def _update_is_patched(self):
        # mark all as patched
        patched = SecurityScan.objects.update(is_patched=True)

        # mark as not patched
        not_patched_ids = SecurityScan.vulnerabilities.through.objects.filter(
            vulnerability__patch_deadline__lte=datetime.now()
        ).values_list(
            'securityscan_id', flat=True
        ).distinct()
        not_patched = SecurityScan.objects.filter(
            id__in=not_patched_ids
        ).update(
            is_patched=False
        )

        self.stdout.write("All scans: {}".format(patched))
        self.stdout.write("Scans marked as patched: {}".format(
            patched - not_patched)
        )

    def handle(self, **options):
        self._update_is_patched()
