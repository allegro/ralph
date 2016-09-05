# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('external_services', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='job',
            name='status',
            field=models.PositiveIntegerField(verbose_name='job status', default=1, choices=[(1, 'queued'), (2, 'finished'), (3, 'failed'), (4, 'started'), (5, 'frozen')]),
        ),
    ]
