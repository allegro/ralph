# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from datetime import datetime

from django.db import migrations


def update_is_patched(apps, schema_editor):
    SecurityScan = apps.get_model("security", "SecurityScan")

    # mark all as patched
    patched = SecurityScan.objects.update(is_patched=True)

    # mark as not patched
    not_patched_ids = (
        SecurityScan.vulnerabilities.through.objects.filter(
            vulnerability__patch_deadline__lte=datetime.now()
        )
        .values_list("securityscan_id", flat=True)
        .distinct()
    )
    not_patched = SecurityScan.objects.filter(id__in=not_patched_ids).update(
        is_patched=False
    )

    print()
    print("All scans: {}".format(SecurityScan.objects.count()))
    print("Scans marked as patched: {}".format(patched - not_patched))


class Migration(migrations.Migration):
    dependencies = [
        ("security", "0006_securityscan_is_patched"),
    ]

    operations = [
        migrations.RunPython(update_is_patched, migrations.RunPython.noop),
    ]
