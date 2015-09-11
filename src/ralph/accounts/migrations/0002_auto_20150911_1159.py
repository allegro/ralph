# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Team',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('name', models.CharField(max_length=255, unique=True, verbose_name='name')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='ralphuser',
            name='team',
            field=models.ForeignKey(to='accounts.Team', blank=True, null=True),
        ),
    ]
