# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('back_office', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='backofficeasset',
            options={'verbose_name_plural': 'Back Office Assets', 'verbose_name': 'Back Office Asset'},
        ),
    ]
