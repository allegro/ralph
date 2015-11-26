# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('security', '0003_auto_20151126_0919'),
    ]

    operations = [
        migrations.AlterField(
            model_name='vulnerability',
            name='name',
            field=models.CharField(verbose_name='name', max_length=1024),
        ),
    ]
