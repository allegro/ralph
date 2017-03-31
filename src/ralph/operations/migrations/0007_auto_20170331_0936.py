# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import ralph.lib.mixins.fields


class Migration(migrations.Migration):

    dependencies = [
        ('operations', '0006_auto_20170323_1530'),
    ]

    operations = [
        migrations.AlterField(
            model_name='operation',
            name='ticket_id',
            field=ralph.lib.mixins.fields.TicketIdField(help_text='External system ticket identifier', max_length=200, blank=True, unique=True, verbose_name='ticket id', null=True),
        ),
    ]
