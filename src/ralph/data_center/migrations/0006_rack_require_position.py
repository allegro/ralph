# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("data_center", "0005_auto_20160121_1133"),
    ]

    operations = [
        migrations.AddField(
            model_name="rack",
            name="require_position",
            field=models.BooleanField(
                default=True,
                help_text="Uncheck if position is optional for this rack (ex. when rack has warehouse-kind role",
            ),
        ),
    ]
