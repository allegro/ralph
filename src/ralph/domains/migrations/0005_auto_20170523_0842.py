# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import ralph.lib.mixins.models


class Migration(migrations.Migration):

    dependencies = [
        ('domains', '0004_auto_20160907_1100'),
    ]

    operations = [
        migrations.CreateModel(
            name='DNSProvider',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255, verbose_name='name', unique=True)),
                ('created', models.DateTimeField(verbose_name='date created', auto_now_add=True)),
                ('modified', models.DateTimeField(verbose_name='last modified', auto_now=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(ralph.lib.mixins.models.AdminAbsoluteUrlMixin, models.Model),
        ),
        migrations.CreateModel(
            name='DomainCategory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255, verbose_name='name', unique=True)),
                ('created', models.DateTimeField(verbose_name='date created', auto_now_add=True)),
                ('modified', models.DateTimeField(verbose_name='last modified', auto_now=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(ralph.lib.mixins.models.AdminAbsoluteUrlMixin, models.Model),
        ),
        migrations.AddField(
            model_name='domain',
            name='domain_type',
            field=models.PositiveIntegerField(choices=[(1, 'None'), (2, 'Business'), (3, 'Business security'), (4, 'technical')], default=2),
        ),
        migrations.AddField(
            model_name='domain',
            name='dns_provider',
            field=models.ForeignKey(to='domains.DNSProvider', help_text="Provider which keeps domain's DNS", blank=True, null=True),
        ),
        migrations.AddField(
            model_name='domain',
            name='domain_category',
            field=models.ForeignKey(to='domains.DomainCategory', blank=True, null=True),
        ),
    ]
