# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("assets", "0008_auto_20160122_1429"),
        ("data_center", "0007_auto_20160225_1818"),
    ]

    # move models from data_center app
    state_operations = [
        migrations.CreateModel(
            name="CloudProject",
            fields=[
                (
                    "baseobject_ptr",
                    models.OneToOneField(
                        primary_key=True,
                        to="assets.BaseObject",
                        auto_created=True,
                        parent_link=True,
                        serialize=False,
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
            bases=("assets.baseobject",),
        ),
        migrations.CreateModel(
            name="VirtualServer",
            fields=[
                (
                    "baseobject_ptr",
                    models.OneToOneField(
                        primary_key=True,
                        to="assets.BaseObject",
                        auto_created=True,
                        parent_link=True,
                        serialize=False,
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
            ],
            options={
                "verbose_name": "Virtual server (VM)",
                "verbose_name_plural": "Virtual servers (VM)",
                "abstract": False,
            },
            bases=("assets.baseobject",),
        ),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(state_operations=state_operations)
    ]
