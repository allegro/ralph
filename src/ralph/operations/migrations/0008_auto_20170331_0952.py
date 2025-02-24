# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("operations", "0007_auto_20170328_1728"),
    ]

    operations = [
        migrations.AlterField(
            model_name="operation",
            name="assignee",
            field=models.ForeignKey(
                verbose_name="assignee",
                blank=True,
                to=settings.AUTH_USER_MODEL,
                null=True,
                related_name="operations",
                on_delete=django.db.models.deletion.PROTECT,
            ),
        ),
    ]
