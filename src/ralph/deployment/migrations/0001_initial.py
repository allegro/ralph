# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django
from django.db import migrations, models

import ralph.deployment.models


class Migration(migrations.Migration):
    dependencies = [
        ("contenttypes", "0002_remove_content_type_name"),
        ("transitions", "0005_auto_20160606_1420"),
    ]

    operations = [
        migrations.CreateModel(
            name="Preboot",
            fields=[
                (
                    "id",
                    models.AutoField(
                        serialize=False,
                        primary_key=True,
                        verbose_name="ID",
                        auto_created=True,
                    ),
                ),
                (
                    "name",
                    models.CharField(unique=True, max_length=255, verbose_name="name"),
                ),
                (
                    "description",
                    models.TextField(
                        blank=True, verbose_name="description", default=""
                    ),
                ),
                (
                    "used_counter",
                    models.PositiveIntegerField(editable=False, default=0),
                ),
            ],
            options={
                "verbose_name": "preboot",
                "verbose_name_plural": "preboots",
                "ordering": ("name",),
            },
        ),
        migrations.CreateModel(
            name="PrebootItem",
            fields=[
                (
                    "id",
                    models.AutoField(
                        serialize=False,
                        primary_key=True,
                        verbose_name="ID",
                        auto_created=True,
                    ),
                ),
                (
                    "name",
                    models.CharField(unique=True, max_length=255, verbose_name="name"),
                ),
                (
                    "description",
                    models.TextField(
                        blank=True, verbose_name="description", default=""
                    ),
                ),
            ],
            options={
                "ordering": ["name"],
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="Deployment",
            fields=[],
            options={
                "proxy": True,
            },
            bases=("transitions.transitionjob",),
        ),
        migrations.CreateModel(
            name="PrebootConfiguration",
            fields=[
                (
                    "prebootitem_ptr",
                    models.OneToOneField(
                        serialize=False,
                        primary_key=True,
                        to="deployment.PrebootItem",
                        parent_link=True,
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
                (
                    "type",
                    models.PositiveIntegerField(
                        choices=[(41, "ipxe"), (42, "kickstart")],
                        verbose_name="type",
                        default=41,
                    ),
                ),
                (
                    "configuration",
                    models.TextField(
                        help_text="All newline characters will be converted to Unix \\n newlines. You can use {{variables}} in the body. Available variables: ralph_instance, deployment_id, kickstart, initrd, kernel, dc, done_url.",
                        blank=True,
                        verbose_name="configuration",
                    ),
                ),
            ],
            options={
                "verbose_name": "preboot configuration",
                "verbose_name_plural": "preboot configuration",
            },
            bases=("deployment.prebootitem",),
        ),
        migrations.CreateModel(
            name="PrebootFile",
            fields=[
                (
                    "prebootitem_ptr",
                    models.OneToOneField(
                        serialize=False,
                        primary_key=True,
                        to="deployment.PrebootItem",
                        parent_link=True,
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
                (
                    "type",
                    models.PositiveIntegerField(
                        choices=[(1, "kernel"), (2, "initrd")],
                        verbose_name="type",
                        default=1,
                    ),
                ),
                (
                    "file",
                    models.FileField(
                        upload_to=ralph.deployment.models.preboot_file_name,
                        null=True,
                        verbose_name="file",
                        default=None,
                        blank=True,
                    ),
                ),
            ],
            options={
                "verbose_name": "preboot file",
                "verbose_name_plural": "preboot files",
            },
            bases=("deployment.prebootitem",),
        ),
        migrations.AddField(
            model_name="prebootitem",
            name="content_type",
            field=models.ForeignKey(
                to="contenttypes.ContentType",
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
            ),
        ),
        migrations.AddField(
            model_name="preboot",
            name="items",
            field=models.ManyToManyField(
                blank=True, verbose_name="files", to="deployment.PrebootItem"
            ),
        ),
    ]
