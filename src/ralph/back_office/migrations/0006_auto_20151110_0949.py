# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('back_office', '0005_auto_20151030_0935'),
    ]

    operations = [
        migrations.CreateModel(
            name='OfficeInfrastructure',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('name', models.CharField(max_length=255, unique=True, verbose_name='name')),
                ('created', models.DateTimeField(verbose_name='date created', auto_now=True)),
                ('modified', models.DateTimeField(verbose_name='last modified', auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Office Infrastructure',
                'verbose_name_plural': 'Office Infrastructures',
            },
        ),
        migrations.AddField(
            model_name='backofficeasset',
            name='office_infrastructure',
            field=models.ForeignKey(null=True, blank=True, to='back_office.OfficeInfrastructure'),
        ),
    ]
