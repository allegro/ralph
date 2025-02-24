# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations

import ralph.lib.transitions.fields


class Migration(migrations.Migration):
    dependencies = [
        ("back_office", "0015_auto_20221207_1445"),
    ]

    operations = [
        migrations.AlterField(
            model_name="backofficeasset",
            name="status",
            field=ralph.lib.transitions.fields.TransitionField(
                default=1,
                choices=[
                    (1, "new"),
                    (2, "in progress"),
                    (3, "waiting for release"),
                    (4, "in use"),
                    (5, "loan"),
                    (6, "damaged"),
                    (7, "liquidated"),
                    (8, "in service"),
                    (9, "installed"),
                    (10, "free"),
                    (11, "reserved"),
                    (12, "sale"),
                    (13, "loan in progress"),
                    (14, "return in progress"),
                    (15, "to find"),
                    (16, "sent"),
                    (17, "to buyout"),
                    (18, "in use team"),
                    (19, "in use test"),
                ],
            ),
        ),
    ]
