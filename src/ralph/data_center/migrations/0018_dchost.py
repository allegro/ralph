# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0019_auto_20160719_1443'),
        ('data_center', '0017_auto_20160719_1530'),
    ]

    operations = [
        migrations.CreateModel(
            name='DCHost',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('assets.baseobject',),
        ),
    ]
