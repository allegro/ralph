# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='baseobject',
            name='parent',
            field=models.ForeignKey(blank=True, to='assets.BaseObject', null=True),
        ),
    ]
