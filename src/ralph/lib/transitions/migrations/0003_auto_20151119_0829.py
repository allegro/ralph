# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('transitions', '0002_transitionshistory'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='transitionshistory',
            options={},
        ),
        migrations.RemoveField(
            model_name='transitionshistory',
            name='transition',
        ),
        migrations.AddField(
            model_name='transitionshistory',
            name='content_type',
            field=models.ForeignKey(default='', to='contenttypes.ContentType'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='transitionshistory',
            name='source',
            field=models.CharField(
                max_length=50, default='', blank=True, null=True
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='transitionshistory',
            name='target',
            field=models.CharField(
                max_length=50, default='', blank=True, null=True
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='transitionshistory',
            name='transition_name',
            field=models.CharField(max_length=255, default=' '),
            preserve_default=False,
        ),
    ]
