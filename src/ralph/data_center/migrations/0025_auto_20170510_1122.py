# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations

import ralph.lib.transitions.fields


class Migration(migrations.Migration):
    dependencies = [
        ("data_center", "0024_auto_20170331_1341"),
    ]

    operations = [
        migrations.AlterField(
            model_name="datacenterasset",
            name="status",
            field=ralph.lib.transitions.fields.TransitionField(
                default=1,
                choices=[
                    (1, "new"),
                    (2, "in use"),
                    (3, "free"),
                    (4, "damaged"),
                    (5, "liquidated"),
                    (6, "to deploy"),
                    (7, "cleaned"),
                    (8, "pre liquidated"),
                ],
            ),
        ),
    ]
