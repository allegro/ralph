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
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('quantity', models.PositiveIntegerField(default=1)),
                ('base_object', models.ForeignKey(related_name='licences', to='assets.BaseObject')),
            ],
        ),
        migrations.CreateModel(
            name='Licence',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('created', models.DateTimeField(verbose_name='date created', auto_now=True)),
                ('modified', models.DateTimeField(verbose_name='last modified', auto_now_add=True)),
                ('number_bought', models.IntegerField(verbose_name='Number of purchased items')),
                ('sn', models.TextField(null=True, blank=True, verbose_name='SN / Key')),
                ('niw', models.CharField(max_length=200, default='N/A', verbose_name='Inventory number', unique=True)),
                ('invoice_date', models.DateField(null=True, blank=True, verbose_name='Invoice date')),
                ('valid_thru', models.DateField(help_text='Leave blank if this licence is perpetual', null=True, blank=True)),
                ('order_no', models.CharField(max_length=50, null=True, blank=True)),
                ('price', models.DecimalField(null=True, blank=True, decimal_places=2, default=0, max_digits=10)),
                ('accounting_id', models.CharField(help_text='Any value to help your accounting department identify this licence', max_length=200, blank=True, null=True)),
                ('provider', models.CharField(max_length=100, null=True, blank=True)),
                ('invoice_no', models.CharField(db_index=True, max_length=128, blank=True, null=True)),
                ('remarks', models.CharField(max_length=1024, null=True, blank=True, default=None, verbose_name='Additional remarks')),
                ('license_details', models.CharField(max_length=1024, blank=True, default='', verbose_name='License details')),
                ('base_objects', models.ManyToManyField(through='licences.BaseObjectLicence', related_name='+', verbose_name='Assigned base objects', to='assets.BaseObject')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='LicenceType',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('name', models.CharField(max_length=255, verbose_name='name', unique=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='LicenceUser',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('quantity', models.PositiveIntegerField(default=1)),
                ('licence', models.ForeignKey(to='licences.Licence')),
                ('user', models.ForeignKey(related_name='licences', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='SoftwareCategory',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('name', models.CharField(max_length=255, verbose_name='name', unique=True)),
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
            field=models.ForeignKey(blank=True, to='assets.Manufacturer', null=True, on_delete=django.db.models.deletion.PROTECT),
        ),
        migrations.AddField(
            model_name='licence',
            name='software_category',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='licences.SoftwareCategory'),
        ),
        migrations.AddField(
            model_name='licence',
            name='users',
            field=models.ManyToManyField(through='licences.LicenceUser', related_name='+', to=settings.AUTH_USER_MODEL),
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
