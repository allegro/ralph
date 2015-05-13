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
                ('location', models.CharField(max_length=128, null=True, blank=True)),
                ('owner', models.ForeignKey(related_name='assets_as_owner', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
                ('user', models.ForeignKey(related_name='assets_as_user', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
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
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=50, verbose_name='name')),
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
