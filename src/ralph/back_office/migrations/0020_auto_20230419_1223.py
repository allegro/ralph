# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime

import django
from django.db import migrations


def forwards_func(apps, schema_editor):
    BackOfficeAsset = apps.get_model("back_office", "BackOfficeAsset")
    today = datetime.date.today()
    BackOfficeAsset.objects.filter(last_status_change__isnull=True).update(
        last_status_change=today
    )


class Migration(migrations.Migration):
    dependencies = [
        ("back_office", "0019_backofficeasset_last_status_change"),
    ]

    operations = [
        migrations.AlterModelManagers(
            name="backofficeasset",
            managers=[
                ("objects", django.db.models.manager.Manager()),
            ],
        ),
        migrations.RunPython(forwards_func),
    ]
