# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations

import ralph.lib.transitions.fields


class Migration(migrations.Migration):
    dependencies = [
        ("access_cards", "0003_auto_20200121_1354"),
    ]

    operations = [
        migrations.AlterField(
            model_name="accesscard",
            name="status",
            field=ralph.lib.transitions.fields.TransitionField(
                default=1,
                choices=[
                    (1, "new"),
                    (2, "in progress"),
                    (3, "lost"),
                    (4, "damaged"),
                    (5, "in use"),
                    (6, "free"),
                    (7, "return in progress"),
                    (8, "liquidated"),
                    (9, "reserved"),
                ],
                help_text="Access card status",
            ),
        ),
    ]
