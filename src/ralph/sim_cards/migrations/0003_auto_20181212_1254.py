# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("sim_cards", "0002_auto_20181123_1138"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="simcard",
            options={"ordering": ("-modified", "-created")},
        ),
    ]
