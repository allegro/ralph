# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('assets', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='BackOfficeAsset',
            fields=[
                ('asset_ptr', models.OneToOneField(serialize=False, to='assets.Asset', primary_key=True, parent_link=True, auto_created=True)),
                ('location', models.CharField(blank=True, max_length=128, null=True)),
                ('owner', models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL, related_name='assets_as_owner', blank=True)),
                ('user', models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL, related_name='assets_as_user', blank=True)),
            ],
            options={
                'verbose_name_plural': 'BO Assets',
                'verbose_name': 'Back Office Asset',
            },
            bases=('assets.asset',),
        ),
        migrations.CreateModel(
            name='Warehouse',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('name', models.CharField(unique=True, max_length=255, verbose_name='name')),
                ('created', models.DateTimeField(auto_now=True, verbose_name='date created')),
                ('modified', models.DateTimeField(auto_now_add=True, verbose_name='last modified')),
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
