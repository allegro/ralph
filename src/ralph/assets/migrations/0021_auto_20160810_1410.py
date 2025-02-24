# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("assets", "0020_auto_20160803_0712"),
    ]

    operations = [
        migrations.AlterField(
            model_name="configurationclass",
            name="path",
            field=models.CharField(
                default="",
                verbose_name="path",
                help_text="path is constructed from name of module and name of class",
                blank=True,
                max_length=511,
                editable=False,
            ),
        ),
    ]
