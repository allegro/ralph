# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('virtual', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cloudflavor',
            name='name',
            field=models.CharField(max_length=255, verbose_name='name'),
        ),
    ]
