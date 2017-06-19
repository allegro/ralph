# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0026_auto_20170510_0840'),
    ]

    operations = [
        migrations.CreateModel(
            name='SCMStatusCheck',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='date created')),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='last modified')),
                ('last_checked', models.DateTimeField(verbose_name='Last SCM check')),
                ('check_result', models.PositiveIntegerField(choices=[(1, 'scm_ok'), (2, 'check_failed'), (3, 'scm_error')], verbose_name='SCM check result')),
                ('base_object', models.OneToOneField(to='assets.BaseObject')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
