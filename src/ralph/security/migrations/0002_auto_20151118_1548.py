# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('security', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='vulnerability',
            name='risk',
            field=models.PositiveIntegerField(choices=[(1, 'low'), (2, 'medium'), (3, 'high')], null=True, blank=True),
        ),
    ]
