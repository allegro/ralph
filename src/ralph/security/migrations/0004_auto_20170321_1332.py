# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations
from django.db.models import Q


def leave_only_last_security_scan(apps, schema_editor):
    SecurityScan = apps.get_model("security", "SecurityScan")

    total_scans = SecurityScan.objects.count()

    base_object_ids = set(SecurityScan.objects.values_list("base_object", flat=True))
    for base_object_id in base_object_ids:
        last_scan_id = (
            SecurityScan.objects.filter(base_object_id=base_object_id)
            .latest("last_scan_date")
            .id
        )
        SecurityScan.objects.filter(
            Q(base_object_id=base_object_id) & ~Q(id=last_scan_id)
        ).delete()

    print()
    print("Total scans: {}".format(total_scans))
    print("Deleted scans: {}".format(total_scans - SecurityScan.objects.count()))


def reverse_func(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("security", "0003_auto_20170110_1352"),
    ]

    operations = [
        migrations.RunPython(leave_only_last_security_scan, reverse_func),
    ]
