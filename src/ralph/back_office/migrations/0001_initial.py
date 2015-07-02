# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='BackOfficeAsset',
            fields=[
                ('asset_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='assets.Asset')),
                ('location', models.CharField(max_length=128, blank=True, null=True)),
                ('owner', models.ForeignKey(to=settings.AUTH_USER_MODEL, null=True, related_name='assets_as_owner', blank=True)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, null=True, related_name='assets_as_user', blank=True)),
            ],
            options={
                'verbose_name': 'Back Office Asset',
                'verbose_name_plural': 'BO Assets',
            },
            bases=('assets.asset',),
        ),
        migrations.CreateModel(
            name='Warehouse',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('name', models.CharField(verbose_name='name', max_length=255, unique=True)),
                ('created', models.DateTimeField(verbose_name='date created', auto_now=True)),
                ('modified', models.DateTimeField(verbose_name='last modified', auto_now_add=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='backofficeasset',
            name='warehouse',
            field=models.ForeignKey(to='back_office.Warehouse', on_delete=django.db.models.deletion.PROTECT),
        ),
    ]
