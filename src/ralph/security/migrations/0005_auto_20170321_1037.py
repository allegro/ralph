# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def assign_last_scan_to_base_object(apps, schema_editor):
    SecurityScan = apps.get_model("security", "SecurityScan")

    total_scans, migrated_scans = SecurityScan.objects.count(), 0

    base_object_ids = SecurityScan.objects.distinct().values_list(
        'base_object', flat=True
    )
    for base_object_id in base_object_ids:
        scans = SecurityScan.objects.filter(base_object_id=base_object_id)
        if scans:
            scan = scans.latest("last_scan_date")
            scan.last_security_scan_id = scan.id
            migrated_scans += 1

    print("Total scans: {}".format(total_scans))
    print("Skipped scans: {}".format(total_scans - migrated_scans))
    print("Migrated scans: {}".format(migrated_scans))


def reverse_func(apps, schema_editor):
    SecurityScan = apps.get_model("security", "SecurityScan")

    SecurityScan.objects.update(last_security_scan=None)


class Migration(migrations.Migration):

    dependencies = [
        ('security', '0004_securityscan_last_security_scan'),
    ]

    operations = [
        migrations.RunPython(assign_last_scan_to_base_object, reverse_func),
    ]
