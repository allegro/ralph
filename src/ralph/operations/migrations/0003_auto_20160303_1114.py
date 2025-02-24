# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

import ralph.lib.mixins.fields


class Migration(migrations.Migration):
    dependencies = [
        ("operations", "0002_auto_20151218_1029"),
    ]

    operations = [
        migrations.AlterField(
            model_name="operation",
            name="status",
            field=models.PositiveIntegerField(
                verbose_name="status",
                default=1,
                choices=[
                    (1, "open"),
                    (2, "in progress"),
                    (3, "resolved"),
                    (4, "closed"),
                ],
            ),
        ),
        migrations.AlterField(
            model_name="operation",
            name="ticket_id",
            field=ralph.lib.mixins.fields.TicketIdField(
                blank=True,
                max_length=200,
                verbose_name="ticket ID",
                null=True,
                help_text="External system ticket identifier",
            ),
        ),
    ]
