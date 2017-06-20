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
                ('id', models.AutoField(serialize=False, primary_key=True, verbose_name='ID', auto_created=True)),
                ('created', models.DateTimeField(verbose_name='date created', auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='last modified')),
                ('last_checked', models.DateTimeField(verbose_name='Last SCM check')),
                ('check_result', models.PositiveIntegerField(verbose_name='SCM check result', choices=[(1, 'OK'), (2, 'Check failed'), (3, 'Error')])),
                ('base_object', models.OneToOneField(to='assets.BaseObject')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
