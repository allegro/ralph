# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

import ralph.trade_marks.models


class Migration(migrations.Migration):
    dependencies = [
        ("trade_marks", "0002_auto_20181005_1446"),
    ]

    operations = [
        migrations.AddField(
            model_name="trademark",
            name="image",
            field=models.ImageField(
                null=True, upload_to=ralph.trade_marks.models.upload_dir, blank=True
            ),
        ),
    ]
