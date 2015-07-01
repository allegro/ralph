# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
from django.conf import settings


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
                ('location', models.CharField(null=True, blank=True, max_length=128)),
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
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('name', models.CharField(verbose_name='name', unique=True, max_length=255)),
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
