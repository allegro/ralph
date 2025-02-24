# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("assets", "0008_auto_20160122_1429"),
        ("data_center", "0007_auto_20160225_1818"),
        ("virtual", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="CloudFlavor",
            fields=[
                (
                    "baseobject_ptr",
                    models.OneToOneField(
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                        parent_link=True,
                        to="assets.BaseObject",
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
                ("name", models.CharField(max_length=255, verbose_name="name")),
                ("flavor_id", models.CharField(unique=True, max_length=100)),
            ],
            options={
                "abstract": False,
            },
            bases=("assets.baseobject",),
        ),
        migrations.CreateModel(
            name="CloudHost",
            fields=[
                (
                    "baseobject_ptr",
                    models.OneToOneField(
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                        parent_link=True,
                        to="assets.BaseObject",
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
                ("host_id", models.CharField(unique=True, max_length=100)),
                ("hostname", models.CharField(max_length=100)),
                ("image_name", models.CharField(blank=True, null=True, max_length=255)),
                (
                    "cloudflavor",
                    models.ForeignKey(
                        verbose_name="Instance Type",
                        to="virtual.CloudFlavor",
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
            ],
            options={
                "verbose_name_plural": "Cloud hosts",
                "verbose_name": "Cloud host",
            },
            bases=("assets.baseobject",),
        ),
        migrations.CreateModel(
            name="CloudProvider",
            fields=[
                (
                    "id",
                    models.AutoField(
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                        auto_created=True,
                    ),
                ),
                (
                    "name",
                    models.CharField(unique=True, max_length=255, verbose_name="name"),
                ),
            ],
            options={
                "verbose_name_plural": "Cloud providers",
                "verbose_name": "Cloud provider",
            },
        ),
        migrations.CreateModel(
            name="VirtualComponent",
            fields=[
                (
                    "id",
                    models.AutoField(
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                        auto_created=True,
                    ),
                ),
                (
                    "base_object",
                    models.ForeignKey(
                        to="assets.BaseObject",
                        related_name="virtualcomponent",
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
                (
                    "model",
                    models.ForeignKey(
                        blank=True,
                        default=None,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        verbose_name="model",
                        to="assets.ComponentModel",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.AddField(
            model_name="cloudproject",
            name="name",
            field=models.CharField(default="", max_length=100),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="cloudproject",
            name="project_id",
            field=models.CharField(default=1, unique=True, max_length=100),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="cloudhost",
            name="cloudprovider",
            field=models.ForeignKey(
                to="virtual.CloudProvider", on_delete=django.db.models.deletion.CASCADE
            ),
        ),
        migrations.AddField(
            model_name="cloudhost",
            name="hypervisor",
            field=models.ForeignKey(
                blank=True,
                null=True,
                to="data_center.DataCenterAsset",
                on_delete=django.db.models.deletion.CASCADE,
            ),
        ),
        migrations.AddField(
            model_name="cloudflavor",
            name="cloudprovider",
            field=models.ForeignKey(
                to="virtual.CloudProvider", on_delete=django.db.models.deletion.CASCADE
            ),
        ),
        migrations.AddField(
            model_name="cloudproject",
            name="cloudprovider",
            field=models.ForeignKey(
                default=1,
                to="virtual.CloudProvider",
                on_delete=django.db.models.deletion.CASCADE,
            ),
            preserve_default=False,
        ),
    ]
