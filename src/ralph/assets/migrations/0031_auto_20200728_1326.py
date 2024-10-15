# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("assets", "0030_auto_20200528_1301"),
    ]

    operations = [
        migrations.AlterField(
            model_name="baseobject",
            name="service_env",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to="assets.ServiceEnvironment",
            ),
        ),
    ]
