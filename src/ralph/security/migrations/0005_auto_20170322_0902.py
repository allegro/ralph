# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('security', '0004_auto_20170321_1332'),
    ]

    operations = [
        migrations.AlterField(
            model_name='securityscan',
            name='base_object',
            field=models.OneToOneField(to='assets.BaseObject'),
        ),
    ]
