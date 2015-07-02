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
            name='BaseObjectLicence',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('quantity', models.PositiveIntegerField(default=1)),
                ('base_object', models.ForeignKey(to='assets.BaseObject', related_name='licences')),
            ],
        ),
        migrations.CreateModel(
            name='Licence',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('created', models.DateTimeField(verbose_name='date created', auto_now=True)),
                ('modified', models.DateTimeField(verbose_name='last modified', auto_now_add=True)),
                ('number_bought', models.IntegerField(verbose_name='Number of purchased items')),
                ('sn', models.TextField(verbose_name='SN / Key', blank=True, null=True)),
                ('niw', models.CharField(verbose_name='Inventory number', max_length=200, unique=True, default='N/A')),
                ('invoice_date', models.DateField(verbose_name='Invoice date', blank=True, null=True)),
                ('valid_thru', models.DateField(blank=True, help_text='Leave blank if this licence is perpetual', null=True)),
                ('order_no', models.CharField(max_length=50, blank=True, null=True)),
                ('price', models.DecimalField(decimal_places=2, max_digits=10, blank=True, null=True, default=0)),
                ('accounting_id', models.CharField(max_length=200, help_text='Any value to help your accounting department identify this licence', null=True, blank=True)),
                ('provider', models.CharField(max_length=100, blank=True, null=True)),
                ('invoice_no', models.CharField(max_length=128, db_index=True, null=True, blank=True)),
                ('remarks', models.CharField(verbose_name='Additional remarks', max_length=1024, blank=True, null=True, default=None)),
                ('license_details', models.CharField(verbose_name='License details', max_length=1024, blank=True, default='')),
                ('base_objects', models.ManyToManyField(to='assets.BaseObject', verbose_name='Assigned base objects', related_name='+', through='licences.BaseObjectLicence')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='LicenceType',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('name', models.CharField(verbose_name='name', max_length=255, unique=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='LicenceUser',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('quantity', models.PositiveIntegerField(default=1)),
                ('licence', models.ForeignKey(to='licences.Licence')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, related_name='licences')),
            ],
        ),
        migrations.CreateModel(
            name='SoftwareCategory',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('name', models.CharField(verbose_name='name', max_length=255, unique=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='licence',
            name='licence_type',
            field=models.ForeignKey(to='licences.LicenceType', on_delete=django.db.models.deletion.PROTECT, help_text="Should be like 'per processor' or 'per machine' and so on. "),
        ),
        migrations.AddField(
            model_name='licence',
            name='manufacturer',
            field=models.ForeignKey(to='assets.Manufacturer', on_delete=django.db.models.deletion.PROTECT, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='licence',
            name='software_category',
            field=models.ForeignKey(to='licences.SoftwareCategory', on_delete=django.db.models.deletion.PROTECT),
        ),
        migrations.AddField(
            model_name='licence',
            name='users',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL, related_name='+', through='licences.LicenceUser'),
        ),
        migrations.AddField(
            model_name='baseobjectlicence',
            name='licence',
            field=models.ForeignKey(to='licences.Licence'),
        ),
        migrations.AlterUniqueTogether(
            name='licenceuser',
            unique_together=set([('licence', 'user')]),
        ),
        migrations.AlterUniqueTogether(
            name='baseobjectlicence',
            unique_together=set([('licence', 'base_object')]),
        ),
    ]
