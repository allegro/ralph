# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("data_center", "0014_custom_move_managment_to_networks"),
    ]

    operations = [
        migrations.AlterField(
            model_name="diskshare",
            name="base_object",
            field=models.ForeignKey(
                related_name="diskshare_set",
                to="assets.BaseObject",
                on_delete=django.db.models.deletion.CASCADE,
            ),
        ),
    ]
