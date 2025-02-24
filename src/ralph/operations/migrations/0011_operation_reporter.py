# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("operations", "0010_auto_20170410_1031"),
    ]

    operations = [
        migrations.AddField(
            model_name="operation",
            name="reporter",
            field=models.ForeignKey(
                null=True,
                blank=True,
                verbose_name="reporter",
                to=settings.AUTH_USER_MODEL,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="reported_operations",
            ),
        ),
    ]
