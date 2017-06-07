# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0026_auto_20170510_0840'),
    ]

    operations = [
        migrations.CreateModel(
            name='SCMScan',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='date created')),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='last modified')),
                ('last_scan_date', models.DateTimeField(verbose_name='Last SCM scan date')),
                ('scan_status', models.PositiveIntegerField(choices=[(1, 'ok'), (2, 'fail'), (3, 'error')], verbose_name='SCM scan status')),
                ('base_object', models.OneToOneField(to='assets.BaseObject')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
