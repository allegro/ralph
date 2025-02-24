# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("virtual", "0012_cloudimage"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="cloudimage",
            options={},
        ),
        migrations.AlterField(
            model_name="cloudimage",
            name="name",
            field=models.CharField(max_length=200),
        ),
    ]
