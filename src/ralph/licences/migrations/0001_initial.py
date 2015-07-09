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
            name='BaseObjectLicence',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('quantity', models.PositiveIntegerField(default=1)),
                ('base_object', models.ForeignKey(to='assets.BaseObject', related_name='licences')),
            ],
        ),
        migrations.CreateModel(
            name='Licence',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now=True, verbose_name='date created')),
                ('modified', models.DateTimeField(auto_now_add=True, verbose_name='last modified')),
                ('number_bought', models.IntegerField(verbose_name='Number of purchased items')),
                ('sn', models.TextField(null=True, blank=True, verbose_name='SN / Key')),
                ('niw', models.CharField(default='N/A', unique=True, max_length=200, verbose_name='Inventory number')),
                ('invoice_date', models.DateField(null=True, blank=True, verbose_name='Invoice date')),
                ('valid_thru', models.DateField(blank=True, help_text='Leave blank if this licence is perpetual', null=True)),
                ('order_no', models.CharField(blank=True, max_length=50, null=True)),
                ('price', models.DecimalField(blank=True, max_digits=10, default=0, decimal_places=2, null=True)),
                ('accounting_id', models.CharField(blank=True, help_text='Any value to help your accounting department identify this licence', max_length=200, null=True)),
                ('provider', models.CharField(blank=True, max_length=100, null=True)),
                ('invoice_no', models.CharField(db_index=True, blank=True, max_length=128, null=True)),
                ('remarks', models.CharField(blank=True, null=True, default=None, max_length=1024, verbose_name='Additional remarks')),
                ('license_details', models.CharField(blank=True, default='', max_length=1024, verbose_name='License details')),
                ('base_objects', models.ManyToManyField(to='assets.BaseObject', through='licences.BaseObjectLicence', related_name='+', verbose_name='Assigned base objects')),
            ],
            options={
                'abstract': False,
            },
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
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, related_name='licences')),
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
            name='licence_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='licences.LicenceType', help_text="Should be like 'per processor' or 'per machine' and so on. "),
        ),
        migrations.AddField(
            model_name='licence',
            name='manufacturer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, null=True, to='assets.Manufacturer', blank=True),
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
