# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('custom_fields', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customfield',
            name='default_value',
            field=models.CharField(max_length=1000, blank=True, help_text='for boolean use "true" or "false"', default='', null=True),
        ),
        migrations.AlterField(
            model_name='customfield',
            name='type',
            field=models.PositiveIntegerField(choices=[(1, 'string'), (2, 'integer'), (3, 'date'), (4, 'boolean'), (5, 'url'), (6, 'choice list')], default=1),
        ),
        migrations.AlterField(
            model_name='customfieldvalue',
            name='custom_field',
            field=models.ForeignKey(verbose_name='key', to='custom_fields.CustomField'),
        ),
    ]
