# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("domains", "0002_auto_20151125_1354"),
    ]

    operations = [
        migrations.AlterField(
            model_name="domain",
            name="name",
            field=models.CharField(
                unique=True,
                help_text="Full domain name",
                max_length=255,
                verbose_name="domain name",
            ),
        ),
    ]
