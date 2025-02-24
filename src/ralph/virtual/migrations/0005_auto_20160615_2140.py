# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("virtual", "0004_virtualserver_status"),
    ]

    operations = [
        migrations.AlterField(
            model_name="virtualcomponent",
            name="base_object",
            field=models.ForeignKey(
                related_name="virtualcomponent_set",
                to="assets.BaseObject",
                on_delete=django.db.models.deletion.CASCADE,
            ),
        ),
    ]
