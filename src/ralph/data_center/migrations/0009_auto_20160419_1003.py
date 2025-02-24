# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django
from django.db import migrations, models

import ralph.lib.mixins.fields


class Migration(migrations.Migration):
    dependencies = [
        ("assets", "0010_auto_20160405_1531"),
        ("data_center", "0008_datacenter_show_on_dashboard"),
    ]

    operations = [
        migrations.CreateModel(
            name="BaseObjectCluster",
            fields=[
                (
                    "id",
                    models.AutoField(
                        serialize=False,
                        verbose_name="ID",
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                ("is_master", models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name="Cluster",
            fields=[
                (
                    "baseobject_ptr",
                    models.OneToOneField(
                        to="assets.BaseObject",
                        parent_link=True,
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
                (
                    "name",
                    models.CharField(verbose_name="name", max_length=255, unique=True),
                ),
                (
                    "base_objects",
                    models.ManyToManyField(
                        through="data_center.BaseObjectCluster",
                        to="assets.BaseObject",
                        verbose_name="Assigned base objects",
                        related_name="_cluster_base_objects_+",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
            bases=("assets.baseobject", models.Model),
        ),
        migrations.CreateModel(
            name="ClusterType",
            fields=[
                (
                    "id",
                    models.AutoField(
                        serialize=False,
                        verbose_name="ID",
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                (
                    "name",
                    models.CharField(verbose_name="name", max_length=255, unique=True),
                ),
            ],
            options={
                "ordering": ["name"],
                "abstract": False,
            },
        ),
        migrations.AddField(
            model_name="cluster",
            name="type",
            field=models.ForeignKey(
                to="data_center.ClusterType",
                on_delete=django.db.models.deletion.CASCADE,
            ),
        ),
        migrations.AddField(
            model_name="baseobjectcluster",
            name="base_object",
            field=ralph.lib.mixins.fields.BaseObjectForeignKey(
                to="assets.BaseObject",
                related_name="clusters",
                on_delete=django.db.models.deletion.CASCADE,
            ),
        ),
        migrations.AddField(
            model_name="baseobjectcluster",
            name="cluster",
            field=models.ForeignKey(
                to="data_center.Cluster", on_delete=django.db.models.deletion.CASCADE
            ),
        ),
        migrations.AlterUniqueTogether(
            name="baseobjectcluster",
            unique_together=set([("cluster", "base_object")]),
        ),
    ]
