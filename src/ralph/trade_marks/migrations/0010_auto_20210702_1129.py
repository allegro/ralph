# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("trade_marks", "0009_auto_20210630_1719"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="design",
            name="type",
        ),
        migrations.RemoveField(
            model_name="patent",
            name="type",
        ),
        migrations.AddField(
            model_name="design",
            name="database_link",
            field=models.URLField(max_length=255, blank=True, null=True),
        ),
        migrations.AddField(
            model_name="patent",
            name="database_link",
            field=models.URLField(max_length=255, blank=True, null=True),
        ),
        migrations.AddField(
            model_name="trademark",
            name="database_link",
            field=models.URLField(max_length=255, blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="design",
            name="classes",
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name="design",
            name="number",
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name="patent",
            name="classes",
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name="patent",
            name="number",
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name="trademark",
            name="classes",
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name="trademark",
            name="number",
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name="trademark",
            name="type",
            field=models.PositiveIntegerField(
                verbose_name="Trade Mark type",
                default=2,
                choices=[(1, "Word"), (2, "Figurative"), (3, "Word - Figurative")],
            ),
        ),
    ]
