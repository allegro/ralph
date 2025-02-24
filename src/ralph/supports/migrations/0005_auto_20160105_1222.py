# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("supports", "0004_auto_20151229_0925"),
    ]

    operations = [
        migrations.AlterField(
            model_name="support",
            name="base_objects",
            field=models.ManyToManyField(
                to="assets.BaseObject",
                through="supports.BaseObjectsSupport",
                related_name="_support_base_objects_+",
            ),
        ),
    ]
