# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("virtual", "0007_auto_20160630_0949"),
    ]

    operations = [
        migrations.AlterField(
            model_name="cloudhost",
            name="host_id",
            field=models.CharField(unique=True, max_length=100, verbose_name="host ID"),
        ),
        migrations.AlterField(
            model_name="cloudhost",
            name="hostname",
            field=models.CharField(max_length=100, verbose_name="hostname"),
        ),
        migrations.AlterField(
            model_name="cloudproject",
            name="project_id",
            field=models.CharField(
                unique=True, max_length=100, verbose_name="project ID"
            ),
        ),
    ]
