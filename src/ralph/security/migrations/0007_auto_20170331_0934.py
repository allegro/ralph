# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from datetime import datetime

from django.db import migrations, models
from django.db.models import Count



def update_is_patched(apps, schema_editor):
    SecurityScan = apps.get_model("security", "SecurityScan")
    is_patched_ids = SecurityScan.vulnerabilities.through.objects.filter(
        vulnerability__patch_deadline__gt=datetime.now()
    ).values_list(
        'securityscan_id', flat=True
    ).distinct()

    patched_scans = SecurityScan.objects.filter(id__in=is_patched_ids).update(
        is_patched=True
    )

    print()
    print("All scans: {}".format(SecurityScan.objects.count()))
    print("Scans marked as patched: {}".format(patched_scans))


class Migration(migrations.Migration):

    dependencies = [
        ('security', '0006_securityscan_is_patched'),
    ]

    operations = [
        migrations.RunPython(update_is_patched, migrations.RunPython.noop),
    ]
