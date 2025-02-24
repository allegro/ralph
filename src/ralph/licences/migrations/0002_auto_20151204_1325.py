# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django
from django.db import migrations

import ralph.lib.mixins.fields


class Migration(migrations.Migration):
    dependencies = [
        ("licences", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="baseobjectlicence",
            name="base_object",
            field=ralph.lib.mixins.fields.BaseObjectForeignKey(
                related_name="licences",
                verbose_name="Asset",
                to="assets.BaseObject",
                on_delete=django.db.models.deletion.CASCADE,
            ),
        ),
    ]
