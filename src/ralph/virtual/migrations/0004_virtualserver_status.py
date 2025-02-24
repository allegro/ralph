# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations

import ralph.lib.transitions.fields


class Migration(migrations.Migration):
    dependencies = [
        ("virtual", "0003_auto_20160606_1442"),
    ]

    operations = [
        migrations.AddField(
            model_name="virtualserver",
            name="status",
            field=ralph.lib.transitions.fields.TransitionField(
                default=1,
                choices=[
                    (1, "new"),
                    (2, "in use"),
                    (3, "to deploy"),
                    (4, "liquidated"),
                ],
            ),
        ),
    ]
