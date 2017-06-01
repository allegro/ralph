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
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('name', models.CharField(max_length=255, unique=True, verbose_name='name')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='date created')),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='last modified')),
            ],
            options={
                'abstract': False,
            },
            bases=(ralph.lib.mixins.models.AdminAbsoluteUrlMixin, models.Model),
        ),
        migrations.CreateModel(
            name='DomainCategory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('name', models.CharField(max_length=255, unique=True, verbose_name='name')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='date created')),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='last modified')),
            ],
            options={
                'abstract': False,
            },
            bases=(ralph.lib.mixins.models.AdminAbsoluteUrlMixin, models.Model),
        ),
        migrations.AddField(
            model_name='domain',
            name='domain_type',
            field=models.PositiveIntegerField(choices=[(1, 'Business'), (2, 'Business security'), (3, 'Technical')], default=1),
        ),
        migrations.AddField(
            model_name='domain',
            name='dns_provider',
            field=models.ForeignKey(to='domains.DNSProvider', null=True, help_text="Provider which keeps domain's DNS", blank=True),
        ),
        migrations.AddField(
            model_name='domain',
            name='domain_category',
            field=models.ForeignKey(to='domains.DomainCategory', null=True, blank=True),
        ),
    ]
