# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('transitions', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transitionconfigmodel',
            name='source',
            field=models.PositiveIntegerField(verbose_name='source', null=True, blank=True),
        ),
    ]
