# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0017_auto_20160510_1436'),
    ]

    operations = [
        migrations.AlterField(
            model_name='configurationclass',
            name='class_name',
            field=models.CharField(max_length=255, help_text='ex. puppet class', validators=[django.core.validators.RegexValidator(regex='\\w+')], verbose_name='class name'),
        ),
    ]
