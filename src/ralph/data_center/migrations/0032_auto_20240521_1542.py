# -*- coding: utf-8 -*-
# Generated by Django 1.11.8 on 2024-05-21 15:42
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("data_center", "0031_auto_20240304_1642"),
    ]

    operations = [
        migrations.AlterField(
            model_name="rack",
            name="server_room",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="racks",
                to="data_center.ServerRoom",
                verbose_name="server room",
            ),
        ),
    ]
