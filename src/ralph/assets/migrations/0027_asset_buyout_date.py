# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0026_auto_20170510_0840'),
    ]

    operations = [
        migrations.AddField(
            model_name='asset',
            name='buyout_date',
            field=models.DateField(blank=True, null=True),
        ),
    ]
