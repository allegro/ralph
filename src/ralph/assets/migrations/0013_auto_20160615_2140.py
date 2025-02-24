# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("assets", "0012_auto_20160606_1409"),
    ]

    operations = [
        migrations.AlterField(
            model_name="ethernet",
            name="base_object",
            field=models.ForeignKey(
                related_name="ethernet_set",
                to="assets.BaseObject",
                on_delete=django.db.models.deletion.CASCADE,
            ),
        ),
        migrations.AlterField(
            model_name="genericcomponent",
            name="base_object",
            field=models.ForeignKey(
                related_name="genericcomponent_set",
                to="assets.BaseObject",
                on_delete=django.db.models.deletion.CASCADE,
            ),
        ),
    ]
