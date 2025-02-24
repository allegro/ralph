# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("deployment", "0005_auto_20180625_1257"),
    ]

    operations = [
        migrations.AlterField(
            model_name="prebootconfiguration",
            name="type",
            field=models.PositiveIntegerField(
                verbose_name="type",
                default=41,
                choices=[
                    (41, "ipxe"),
                    (42, "kickstart"),
                    (43, "preseed"),
                    (44, "script"),
                    (45, "meta_data"),
                    (46, "user_data"),
                ],
            ),
        ),
    ]
