# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django
from django.db import migrations, models

import ralph.lib.mixins.models
import ralph.lib.transitions.fields


class Migration(migrations.Migration):
    dependencies = [
        ("assets", "0012_auto_20160606_1409"),
        ("tests", "0005_bar_foos"),
    ]

    operations = [
        migrations.CreateModel(
            name="AsyncOrder",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        auto_created=True,
                        serialize=False,
                        primary_key=True,
                    ),
                ),
                (
                    "status",
                    ralph.lib.transitions.fields.TransitionField(
                        choices=[(1, "new"), (2, "to_send"), (3, "sended")], default=1
                    ),
                ),
                ("name", models.CharField(max_length=100)),
                ("counter", models.PositiveSmallIntegerField(default=1)),
                ("username", models.CharField(max_length=100, blank=True, null=True)),
                (
                    "foo",
                    models.ForeignKey(
                        blank=True,
                        to="tests.Foo",
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
            ],
            bases=(ralph.lib.mixins.models.AdminAbsoluteUrlMixin, models.Model),
        ),
        migrations.CreateModel(
            name="PolymorphicTestModel",
            fields=[
                (
                    "baseobject_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        serialize=False,
                        primary_key=True,
                        to="assets.BaseObject",
                        parent_link=True,
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
                ("hostname", models.CharField(max_length=50)),
            ],
            options={
                "abstract": False,
            },
            bases=(ralph.lib.mixins.models.AdminAbsoluteUrlMixin, "assets.baseobject"),
        ),
        migrations.AddField(
            model_name="order",
            name="remarks",
            field=models.CharField(max_length=255, blank=True, default=""),
        ),
    ]
