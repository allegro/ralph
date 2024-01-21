# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime


def forwards_func(apps, schema_editor):
    BackOfficeAsset = apps.get_model('back_office', 'BackOfficeAsset')
    today = datetime.date.today()
    BackOfficeAsset.objects.filter(last_status_change__isnull=True).update(last_status_change=today)


class Migration(migrations.Migration):

    dependencies = [
        ('back_office', '0019_backofficeasset_last_status_change'),
    ]

    operations = [
        migrations.RunPython(forwards_func),
    ]
