# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("data_center", "0003_auto_20151126_2222"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="datacenter",
            options={"ordering": ["name"]},
        ),
        migrations.AlterModelOptions(
            name="serverroom",
            options={"ordering": ["name"]},
        ),
    ]
