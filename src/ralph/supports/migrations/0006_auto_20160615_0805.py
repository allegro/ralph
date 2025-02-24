# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django
from django.db import migrations, models

import ralph.lib.mixins.fields


class Migration(migrations.Migration):
    dependencies = [
        ("supports", "0005_auto_20160105_1222"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="baseobjectssupport",
            options={},
        ),
        migrations.AlterModelTable(
            name="baseobjectssupport",
            table=None,
        ),
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name="baseobjectssupport",
                    name="baseobject",
                    field=ralph.lib.mixins.fields.BaseObjectForeignKey(
                        default=0,
                        verbose_name="Asset",
                        to="assets.BaseObject",
                        related_name="supports",
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                    preserve_default=False,
                ),
                migrations.AddField(
                    model_name="baseobjectssupport",
                    name="support",
                    field=models.ForeignKey(
                        default=0,
                        to="supports.Support",
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                    preserve_default=False,
                ),
            ],
            database_operations=[],
        ),
    ]
