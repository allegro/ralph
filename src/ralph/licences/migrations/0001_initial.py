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
            name='Licence',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now=True, verbose_name='date created')),
                ('modified', models.DateTimeField(auto_now_add=True, verbose_name='last modified')),
                ('number_bought', models.IntegerField(verbose_name='Number of purchased items')),
                ('sn', models.TextField(null=True, blank=True, verbose_name='SN / Key')),
                ('niw', models.CharField(unique=True, max_length=200, default='N/A', verbose_name='Inventory number')),
                ('invoice_date', models.DateField(null=True, blank=True, verbose_name='Invoice date')),
                ('valid_thru', models.DateField(null=True, blank=True, help_text='Leave blank if this licence is perpetual')),
                ('order_no', models.CharField(null=True, max_length=50, blank=True)),
                ('price', models.DecimalField(max_digits=10, null=True, decimal_places=2, blank=True, default=0)),
                ('accounting_id', models.CharField(null=True, max_length=200, blank=True, help_text='Any value to help your accounting department identify this licence')),
                ('provider', models.CharField(null=True, max_length=100, blank=True)),
                ('invoice_no', models.CharField(db_index=True, null=True, max_length=128, blank=True)),
                ('remarks', models.CharField(null=True, max_length=1024, blank=True, default=None, verbose_name='Additional remarks')),
                ('license_details', models.CharField(max_length=1024, blank=True, default='', verbose_name='License details')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='LicenceAsset',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('quantity', models.PositiveIntegerField(default=1)),
                ('asset', models.ForeignKey(related_name='licences', to='assets.Asset')),
                ('licence', models.ForeignKey(to='licences.Licence')),
            ],
        ),
        migrations.CreateModel(
            name='LicenceType',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('name', models.CharField(unique=True, max_length=255, verbose_name='name')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='LicenceUser',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('quantity', models.PositiveIntegerField(default=1)),
                ('licence', models.ForeignKey(to='licences.Licence')),
                ('user', models.ForeignKey(related_name='licences', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='SoftwareCategory',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('name', models.CharField(unique=True, max_length=255, verbose_name='name')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='licence',
            name='assets',
            field=models.ManyToManyField(related_name='+', through='licences.LicenceAsset', to='assets.Asset', verbose_name='Assigned Assets'),
        ),
        migrations.AddField(
            model_name='licence',
            name='licence_type',
            field=models.ForeignKey(to='licences.LicenceType', help_text="Should be like 'per processor' or 'per machine' and so on. ", on_delete=django.db.models.deletion.PROTECT),
        ),
        migrations.AddField(
            model_name='licence',
            name='manufacturer',
            field=models.ForeignKey(null=True, blank=True, to='assets.Manufacturer', on_delete=django.db.models.deletion.PROTECT),
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
