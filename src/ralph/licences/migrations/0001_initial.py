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
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('quantity', models.PositiveIntegerField(default=1)),
                ('base_object', models.ForeignKey(related_name='licences', to='assets.BaseObject')),
            ],
        ),
        migrations.CreateModel(
            name='Licence',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('created', models.DateTimeField(verbose_name='date created', auto_now=True)),
                ('modified', models.DateTimeField(verbose_name='last modified', auto_now_add=True)),
                ('number_bought', models.IntegerField(verbose_name='Number of purchased items')),
                ('sn', models.TextField(verbose_name='SN / Key', blank=True, null=True)),
                ('niw', models.CharField(verbose_name='Inventory number', default='N/A', unique=True, max_length=200)),
                ('invoice_date', models.DateField(verbose_name='Invoice date', blank=True, null=True)),
                ('valid_thru', models.DateField(blank=True, help_text='Leave blank if this licence is perpetual', null=True)),
                ('order_no', models.CharField(null=True, blank=True, max_length=50)),
                ('price', models.DecimalField(default=0, max_digits=10, decimal_places=2, blank=True, null=True)),
                ('accounting_id', models.CharField(null=True, blank=True, help_text='Any value to help your accounting department identify this licence', max_length=200)),
                ('provider', models.CharField(null=True, blank=True, max_length=100)),
                ('invoice_no', models.CharField(null=True, db_index=True, blank=True, max_length=128)),
                ('remarks', models.CharField(verbose_name='Additional remarks', default=None, null=True, blank=True, max_length=1024)),
                ('license_details', models.CharField(verbose_name='License details', default='', blank=True, max_length=1024)),
                ('base_objects', models.ManyToManyField(verbose_name='Assigned base objects', related_name='+', through='licences.BaseObjectLicence', to='assets.BaseObject')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='LicenceType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('name', models.CharField(verbose_name='name', unique=True, max_length=255)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='LicenceUser',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('quantity', models.PositiveIntegerField(default=1)),
                ('licence', models.ForeignKey(to='licences.Licence')),
                ('user', models.ForeignKey(related_name='licences', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='SoftwareCategory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('name', models.CharField(verbose_name='name', unique=True, max_length=255)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='licence',
            name='licence_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, help_text="Should be like 'per processor' or 'per machine' and so on. ", to='licences.LicenceType'),
        ),
        migrations.AddField(
            model_name='licence',
            name='manufacturer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, blank=True, to='assets.Manufacturer', null=True),
        ),
        migrations.AddField(
            model_name='licence',
            name='software_category',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='licences.SoftwareCategory'),
        ),
        migrations.AddField(
            model_name='licence',
            name='users',
            field=models.ManyToManyField(related_name='+', through='licences.LicenceUser', to=settings.AUTH_USER_MODEL),
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
