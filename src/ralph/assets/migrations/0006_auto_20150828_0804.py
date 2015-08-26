# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('assets', '0005_merge'),
    ]

    operations = [
        migrations.CreateModel(
            name='BusinessSegment',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('name', models.CharField(unique=True, verbose_name='name', max_length=255)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ProfitCenter',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('name', models.CharField(unique=True, verbose_name='name', max_length=255)),
                ('business_segment', models.ForeignKey(to='assets.BusinessSegment')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='service',
            name='business_owners',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL, blank=True, related_name='services_business_owner'),
        ),
        migrations.AddField(
            model_name='service',
            name='technical_owners',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL, blank=True, related_name='services_technical_owner'),
        ),
        migrations.RemoveField(
            model_name='service',
            name='profit_center',
        ),
        migrations.AddField(
            model_name='service',
            name='profit_center',
            field=models.ForeignKey(blank=True, null=True, to='assets.ProfitCenter'),
        ),
    ]
