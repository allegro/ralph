# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_center', '0004_auto_20151204_0758'),
    ]

    operations = [
        migrations.AddField(
            model_name='rack',
            name='require_position',
            field=models.BooleanField(help_text='Uncheck if position is optional for this rack (ex. when rack has warehouse-kind role', default=True),
        ),
    ]
