# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("data_importer", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="importedobjects",
            name="created",
            field=models.DateTimeField(auto_now_add=True, verbose_name="date created"),
        ),
        migrations.AlterField(
            model_name="importedobjects",
            name="modified",
            field=models.DateTimeField(auto_now=True, verbose_name="last modified"),
        ),
    ]
