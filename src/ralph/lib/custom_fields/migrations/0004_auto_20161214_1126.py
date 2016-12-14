# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('custom_fields', '0003_auto_20160804_1305'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customfield',
            name='choices',
            field=models.TextField(null=True, verbose_name='choices', help_text='available choices for `choices list` separated by |', blank=True),
        ),
    ]
