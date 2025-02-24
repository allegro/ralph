# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("data_center", "0017_auto_20160719_1530"),
    ]

    operations = [
        migrations.AlterField(
            model_name="rack",
            name="server_room",
            field=models.ForeignKey(
                verbose_name="server room",
                null=True,
                to="data_center.ServerRoom",
                on_delete=django.db.models.deletion.CASCADE,
            ),
        ),
    ]
