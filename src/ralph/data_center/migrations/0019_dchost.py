# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("assets", "0019_auto_20160719_1443"),
        ("data_center", "0018_auto_20160729_1401"),
    ]

    operations = [
        migrations.CreateModel(
            name="DCHost",
            fields=[],
            options={
                "proxy": True,
            },
            bases=("assets.baseobject",),
        ),
    ]
