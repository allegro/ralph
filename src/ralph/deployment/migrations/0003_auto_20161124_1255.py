# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('deployment', '0002_auto_20160816_1112'),
    ]

    operations = [
        migrations.AlterField(
            model_name='prebootfile',
            name='type',
            field=models.PositiveIntegerField(default=1, choices=[(1, 'kernel'), (2, 'initrd'), (3, 'netboot')], verbose_name='type'),
        ),
    ]
