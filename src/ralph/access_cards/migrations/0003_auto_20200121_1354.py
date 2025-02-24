# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations

import ralph.lib.transitions.fields


class Migration(migrations.Migration):
    dependencies = [
        ("access_cards", "0002_auto_20200116_1248"),
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
                    (7, "return in progres"),
                    (8, "liquidated"),
                ],
                help_text="Access card status",
            ),
        ),
    ]
