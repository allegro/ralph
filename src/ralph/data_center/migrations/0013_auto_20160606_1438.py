# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime

from django.db import migrations, models

import ralph.lib.mixins.fields
import ralph.lib.transitions.fields


class Migration(migrations.Migration):
    dependencies = [
        ("data_center", "0012_custom_move_to_networks"),
    ]

    operations = [
        migrations.AddField(
            model_name="cluster",
            name="hostname",
            field=ralph.lib.mixins.fields.NullableCharField(
                blank=True,
                unique=True,
                max_length=255,
                null=True,
                verbose_name="hostname",
            ),
        ),
        migrations.AddField(
            model_name="cluster",
            name="status",
            field=ralph.lib.transitions.fields.TransitionField(
                choices=[(1, "in use"), (2, "for deploy")], default=1
            ),
        ),
        migrations.AddField(
            model_name="clustertype",
            name="show_master_summary",
            field=models.BooleanField(
                help_text="show master information on cluster page, ex. hostname, model, location etc.",
                default=False,
            ),
        ),
        migrations.AddField(
            model_name="diskshare",
            name="created",
            field=models.DateTimeField(
                default=datetime.datetime(2016, 6, 6, 14, 38, 42, 553494),
                verbose_name="date created",
                auto_now_add=True,
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="diskshare",
            name="modified",
            field=models.DateTimeField(
                default=datetime.datetime(2016, 6, 6, 14, 38, 45, 192509),
                verbose_name="last modified",
                auto_now=True,
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="cluster",
            name="name",
            field=models.CharField(
                blank=True, null=True, max_length=255, verbose_name="name"
            ),
        ),
    ]
