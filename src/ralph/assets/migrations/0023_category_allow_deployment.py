# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("assets", "0022_auto_20160823_0921"),
    ]

    operations = [
        migrations.AddField(
            model_name="category",
            name="allow_deployment",
            field=models.BooleanField(default=False),
        ),
    ]
