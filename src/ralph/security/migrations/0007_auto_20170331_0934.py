# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.db.models import Count



def update_is_patched(apps, schema_editor):
    SecurityScan = apps.get_model("security", "SecurityScan")
    all_scans = SecurityScan.objects.count()
    change_count = SecurityScan.objects.annotate(
        vuls_count=Count('vulnerabilities')
    ).filter(vuls_count=0).update(is_patched=True)

    print()
    print("All scans: {}".format(all_scans))
    print("Scans marked as patched: {}".format(change_count))


def reverse_func(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('security', '0006_securityscan_is_patched'),
    ]

    operations = [
        migrations.RunPython(update_is_patched, reverse_func),
    ]
