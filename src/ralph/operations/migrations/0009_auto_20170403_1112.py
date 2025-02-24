# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations

import ralph.lib.mixins.fields


class Migration(migrations.Migration):
    dependencies = [
        ("operations", "0008_auto_20170331_0952"),
    ]

    operations = [
        migrations.AlterField(
            model_name="operation",
            name="ticket_id",
            field=ralph.lib.mixins.fields.TicketIdField(
                null=True,
                max_length=200,
                verbose_name="ticket id",
                unique=True,
                blank=True,
                help_text="External system ticket identifier",
            ),
        ),
    ]
