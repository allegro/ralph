# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations

import ralph.lib.mixins.fields


class Migration(migrations.Migration):
    dependencies = [
        ("operations", "0004_auto_20160307_1138"),
    ]

    operations = [
        migrations.AlterField(
            model_name="operation",
            name="ticket_id",
            field=ralph.lib.mixins.fields.TicketIdField(
                null=True,
                unique=False,
                max_length=200,
                verbose_name="ticket id",
                blank=True,
                help_text="External system ticket identifier",
            ),
        ),
    ]
