# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('back_office', '0003_auto_20151014_1211'),
    ]

    operations = [
        migrations.CreateModel(
            name='AssetHolder',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=75, verbose_name='name')),
                ('created', models.DateTimeField(auto_now=True, verbose_name='date created')),
                ('modified', models.DateTimeField(auto_now_add=True, verbose_name='last modified')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='backofficeasset',
            name='property_of',
            field=models.ForeignKey(blank=True, to='back_office.AssetHolder', null=True, on_delete=django.db.models.deletion.PROTECT),
        ),
    ]
