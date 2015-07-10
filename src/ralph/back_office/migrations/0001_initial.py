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
                ('asset_ptr', models.OneToOneField(primary_key=True, parent_link=True, to='assets.Asset', serialize=False, auto_created=True)),
                ('location', models.CharField(max_length=128, null=True, blank=True)),
                ('owner', models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True, related_name='assets_as_owner')),
                ('user', models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True, related_name='assets_as_user')),
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
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('name', models.CharField(max_length=255, verbose_name='name', unique=True)),
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
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='back_office.Warehouse'),
        ),
    ]
