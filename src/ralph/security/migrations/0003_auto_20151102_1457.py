# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('security', '0002_auto_20151030_1311'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='vulnerability',
            name='compliance_patching_policy',
        ),
        migrations.AlterField(
            model_name='vulnerability',
            name='name',
            field=models.CharField(unique=True, verbose_name='name', max_length=255),
        ),
    ]
