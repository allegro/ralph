# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

import ralph.lib.mixins.fields


class Migration(migrations.Migration):
    dependencies = [
        ("deployment", "0004_auto_20161128_1359"),
    ]

    operations = [
        migrations.AlterField(
            model_name="prebootconfiguration",
            name="configuration",
            field=ralph.lib.mixins.fields.NUMP(
                models.TextField(blank=True),
                fields_to_ignore=("help_text", "verbose_name"),
            ),
        ),
    ]
