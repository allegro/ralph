# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime

import django
from django.db import migrations, models

import ralph.lib.mixins.fields


class Migration(migrations.Migration):
    dependencies = [
        ("data_center", "0013_auto_20160606_1438"),
        ("virtual", "0002_auto_20160226_0826"),
    ]

    operations = [
        migrations.CreateModel(
            name="VirtualServerType",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        serialize=False,
                        primary_key=True,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=75, verbose_name="name")),
                (
                    "created",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="date created"
                    ),
                ),
                (
                    "modified",
                    models.DateTimeField(auto_now=True, verbose_name="last modified"),
                ),
            ],
            options={
                "ordering": ["name"],
                "abstract": False,
            },
        ),
        migrations.AddField(
            model_name="virtualcomponent",
            name="created",
            field=models.DateTimeField(
                auto_now_add=True,
                default=datetime.datetime(2016, 6, 6, 14, 41, 55, 331734),
                verbose_name="date created",
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="virtualcomponent",
            name="modified",
            field=models.DateTimeField(
                auto_now=True,
                default=datetime.datetime(2016, 6, 6, 14, 41, 58, 683625),
                verbose_name="last modified",
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="virtualserver",
            name="cluster",
            field=models.ForeignKey(
                blank=True,
                to="data_center.Cluster",
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
            ),
        ),
        migrations.AddField(
            model_name="virtualserver",
            name="hostname",
            field=ralph.lib.mixins.fields.NullableCharField(
                null=True,
                default=None,
                blank=True,
                max_length=255,
                verbose_name="hostname",
                unique=True,
            ),
        ),
        migrations.AddField(
            model_name="virtualserver",
            name="sn",
            field=models.CharField(
                max_length=200, default=1, verbose_name="SN", unique=True
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="virtualserver",
            name="type",
            field=models.ForeignKey(
                default=1,
                to="virtual.VirtualServerType",
                related_name="virtual_servers",
                on_delete=django.db.models.deletion.CASCADE,
            ),
            preserve_default=False,
        ),
    ]
