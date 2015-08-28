# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import ralph.lib.mixins.models
from django.conf import settings
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0001_initial'),
        ('accounts', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='BaseObjectLicence',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('quantity', models.PositiveIntegerField(default=1)),
                ('base_object', models.ForeignKey(to='assets.BaseObject', related_name='licences')),
            ],
        ),
        migrations.CreateModel(
            name='Licence',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('created', models.DateTimeField(verbose_name='date created', auto_now=True)),
                ('modified', models.DateTimeField(verbose_name='last modified', auto_now_add=True)),
                ('number_bought', models.IntegerField(verbose_name='Number of purchased items')),
                ('sn', models.TextField(null=True, verbose_name='SN / Key', blank=True)),
                ('niw', models.CharField(verbose_name='Inventory number', max_length=200, default='N/A', unique=True)),
                ('invoice_date', models.DateField(null=True, verbose_name='Invoice date', blank=True)),
                ('valid_thru', models.DateField(null=True, help_text='Leave blank if this licence is perpetual', blank=True)),
                ('order_no', models.CharField(null=True, blank=True, max_length=50)),
                ('price', models.DecimalField(null=True, decimal_places=2, blank=True, default=0, max_digits=10)),
                ('accounting_id', models.CharField(null=True, help_text='Any value to help your accounting department identify this licence', blank=True, max_length=200)),
                ('provider', models.CharField(null=True, blank=True, max_length=100)),
                ('invoice_no', models.CharField(null=True, blank=True, db_index=True, max_length=128)),
                ('remarks', models.TextField(blank=True)),
                ('license_details', models.CharField(verbose_name='License details', blank=True, default='', max_length=1024)),
                ('base_objects', models.ManyToManyField(to='assets.BaseObject', verbose_name='Assigned base objects', through='licences.BaseObjectLicence', related_name='+')),
            ],
            options={
                'abstract': False,
            },
            bases=(ralph.lib.mixins.models.AdminAbsoluteUrlMixin, models.Model),
        ),
        migrations.CreateModel(
            name='LicenceType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('name', models.CharField(verbose_name='name', max_length=255, unique=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='LicenceUser',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('quantity', models.PositiveIntegerField(default=1)),
                ('licence', models.ForeignKey(to='licences.Licence')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, related_name='licences')),
            ],
        ),
        migrations.CreateModel(
            name='SoftwareCategory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('name', models.CharField(verbose_name='name', max_length=255, unique=True)),
            ],
            options={
                'verbose_name_plural': 'software categories',
            },
        ),
        migrations.AddField(
            model_name='licence',
            name='licence_type',
            field=models.ForeignKey(to='licences.LicenceType', help_text="Should be like 'per processor' or 'per machine' and so on. ", on_delete=django.db.models.deletion.PROTECT),
        ),
        migrations.AddField(
            model_name='licence',
            name='manufacturer',
            field=models.ForeignKey(null=True, to='assets.Manufacturer', on_delete=django.db.models.deletion.PROTECT, blank=True),
        ),
        migrations.AddField(
            model_name='licence',
            name='region',
            field=models.ForeignKey(to='accounts.Region'),
        ),
        migrations.AddField(
            model_name='licence',
            name='software_category',
            field=models.ForeignKey(to='licences.SoftwareCategory', on_delete=django.db.models.deletion.PROTECT),
        ),
        migrations.AddField(
            model_name='licence',
            name='users',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL, through='licences.LicenceUser', related_name='+'),
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
