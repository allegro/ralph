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
            name='Licence',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now=True, verbose_name='date created')),
                ('modified', models.DateTimeField(auto_now_add=True, verbose_name='last modified')),
                ('number_bought', models.IntegerField(verbose_name='Number of purchased items')),
                ('sn', models.TextField(null=True, verbose_name='SN / Key', blank=True)),
                ('niw', models.CharField(default='N/A', unique=True, max_length=200, verbose_name='Inventory number')),
                ('invoice_date', models.DateField(null=True, verbose_name='Invoice date', blank=True)),
                ('valid_thru', models.DateField(help_text='Leave blank if this licence is perpetual', null=True, blank=True)),
                ('order_no', models.CharField(max_length=50, null=True, blank=True)),
                ('price', models.DecimalField(default=0, null=True, max_digits=10, decimal_places=2, blank=True)),
                ('accounting_id', models.CharField(help_text='Any value to help your accounting department identify this licence', max_length=200, null=True, blank=True)),
                ('provider', models.CharField(max_length=100, null=True, blank=True)),
                ('invoice_no', models.CharField(db_index=True, max_length=128, null=True, blank=True)),
                ('remarks', models.CharField(default=None, max_length=1024, null=True, verbose_name='Additional remarks', blank=True)),
                ('license_details', models.CharField(default='', max_length=1024, verbose_name='License details', blank=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='LicenceAsset',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('quantity', models.PositiveIntegerField(default=1)),
                ('asset', models.ForeignKey(related_name='licences', to='assets.Asset')),
                ('licence', models.ForeignKey(to='licences.Licence')),
            ],
        ),
        migrations.CreateModel(
            name='LicenceType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=50, verbose_name='name')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='LicenceUser',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('quantity', models.PositiveIntegerField(default=1)),
                ('licence', models.ForeignKey(to='licences.Licence')),
                ('user', models.ForeignKey(related_name='licences', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='SoftwareCategory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=50, verbose_name='name')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='licence',
            name='assets',
            field=models.ManyToManyField(related_name='+', verbose_name='Assigned Assets', through='licences.LicenceAsset', to='assets.Asset'),
        ),
        migrations.AddField(
            model_name='licence',
            name='licence_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='licences.LicenceType', help_text="Should be like 'per processor' or 'per machine' and so on. "),
        ),
        migrations.AddField(
            model_name='licence',
            name='manufacturer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, blank=True, to='assets.Manufacturer', null=True),
        ),
        migrations.AddField(
            model_name='licence',
            name='software_category',
            field=models.ForeignKey(to='licences.SoftwareCategory', on_delete=django.db.models.deletion.PROTECT),
        ),
        migrations.AddField(
            model_name='licence',
            name='users',
            field=models.ManyToManyField(related_name='+', through='licences.LicenceUser', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterUniqueTogether(
            name='licenceuser',
            unique_together=set([('licence', 'user')]),
        ),
        migrations.AlterUniqueTogether(
            name='licenceasset',
            unique_together=set([('licence', 'asset')]),
        ),
    ]
