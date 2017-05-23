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
                ('name', models.CharField(verbose_name='name', unique=True, max_length=255)),
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
                ('name', models.CharField(verbose_name='name', unique=True, max_length=255)),
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
            field=models.PositiveIntegerField(default=1, choices=[(1, 'Business'), (2, 'Business security'), (3, 'technical')]),
        ),
        migrations.AddField(
            model_name='domain',
            name='dns_provider',
            field=models.ForeignKey(blank=True, help_text="Provider which keeps domain's DNS", null=True, to='domains.DNSProvider'),
        ),
        migrations.AddField(
            model_name='domain',
            name='domain_category',
            field=models.ForeignKey(blank=True, null=True, to='domains.DomainCategory'),
        ),
    ]
