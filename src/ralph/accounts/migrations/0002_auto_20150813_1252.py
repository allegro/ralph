# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Region',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('name', models.CharField(max_length=255, unique=True, verbose_name='name')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='ralphuser',
            name='regions',
            field=models.ManyToManyField(to='accounts.Region'),
        ),
    ]
