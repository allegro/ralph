# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('security', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='securityscan',
            name='asset',
            field=models.ForeignKey(to='assets.BaseObject', null=True),
        ),
    ]
