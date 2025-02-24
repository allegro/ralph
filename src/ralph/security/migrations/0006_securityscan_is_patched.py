# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("security", "0005_auto_20170322_0902"),
    ]

    operations = [
        migrations.AddField(
            model_name="securityscan",
            name="is_patched",
            field=models.BooleanField(default=False),
        ),
    ]
