# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0005_auto_20170814_1636"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="ralphuser",
            name="gender",
        ),
    ]
