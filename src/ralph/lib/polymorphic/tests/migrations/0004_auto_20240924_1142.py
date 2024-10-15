# -*- coding: utf-8 -*-
# Generated by Django 1.11.8 on 2024-09-24 11:42
from __future__ import unicode_literals

from django.db import migrations
import ralph.lib.polymorphic.fields


class Migration(migrations.Migration):

    dependencies = [
        ("polymorphic_tests", "0003_auto_20240506_1133"),
    ]

    operations = [
        migrations.AlterField(
            model_name="somem2mmodel",
            name="polymorphics",
            field=ralph.lib.polymorphic.fields.PolymorphicManyToManyField(
                related_name="some_m2m", to="polymorphic_tests.PolymorphicModelBaseTest"
            ),
        ),
    ]
