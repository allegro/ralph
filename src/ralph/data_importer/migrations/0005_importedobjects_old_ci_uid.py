# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("data_importer", "0004_auto_20160728_1046"),
    ]

    operations = [
        migrations.AddField(
            model_name="importedobjects",
            name="old_ci_uid",
            field=models.CharField(
                max_length=255, null=True, blank=True, db_index=True
            ),
        ),
    ]
