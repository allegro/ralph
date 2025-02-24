# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accessories", "0002_auto_20210510_1246"),
    ]

    operations = [
        migrations.AlterField(
            model_name="accessory",
            name="accessory_name",
            field=models.CharField(max_length=255, help_text="Accessory name"),
        ),
    ]
