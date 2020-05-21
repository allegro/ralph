# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('domains', '0006_auto_20180725_1216'),
    ]

    operations = [
        migrations.AlterField(
            model_name='domain',
            name='domain_status',
            field=models.PositiveIntegerField(default=1, choices=[(1, 'Active'), (2, 'Pending lapse'), (3, 'Pending transfer away'), (4, 'Lapsed (inactive)'), (5, 'Transferred away')]),
        ),
    ]
