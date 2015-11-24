# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings
import django.db.models.deletion
import ralph.lib.mixins.models


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('back_office', '0001_initial'),
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='BaseObjectLicence',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('quantity', models.PositiveIntegerField(default=1)),
            ],
        ),
        migrations.CreateModel(
            name='Licence',
            fields=[
                ('baseobject_ptr', models.OneToOneField(primary_key=True, to='assets.BaseObject', auto_created=True, serialize=False, parent_link=True)),
                ('number_bought', models.IntegerField(verbose_name='Number of purchased items')),
                ('sn', models.TextField(blank=True, verbose_name='SN / Key', null=True)),
                ('niw', models.CharField(verbose_name='Inventory number', unique=True, max_length=200, default='N/A')),
                ('invoice_date', models.DateField(blank=True, verbose_name='Invoice date', null=True)),
                ('valid_thru', models.DateField(blank=True, null=True, help_text='Leave blank if this licence is perpetual')),
                ('order_no', models.CharField(blank=True, max_length=50, null=True)),
                ('price', models.DecimalField(blank=True, max_digits=10, default=0, null=True, decimal_places=2)),
                ('accounting_id', models.CharField(blank=True, max_length=200, null=True, help_text='Any value to help your accounting department identify this licence')),
                ('provider', models.CharField(blank=True, max_length=100, null=True)),
                ('invoice_no', models.CharField(blank=True, max_length=128, null=True, db_index=True)),
                ('license_details', models.CharField(blank=True, verbose_name='License details', max_length=1024, default='')),
                ('base_objects', models.ManyToManyField(to='assets.BaseObject', verbose_name='Assigned base objects', related_name='_base_objects_+', through='licences.BaseObjectLicence')),
                ('budget_info', models.ForeignKey(blank=True, to='assets.BudgetInfo', default=None, on_delete=django.db.models.deletion.PROTECT, null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(ralph.lib.mixins.models.AdminAbsoluteUrlMixin, 'assets.baseobject', models.Model),
        ),
        migrations.CreateModel(
            name='LicenceType',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('name', models.CharField(verbose_name='name', unique=True, max_length=255)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='LicenceUser',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('quantity', models.PositiveIntegerField(default=1)),
                ('licence', models.ForeignKey(to='licences.Licence')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, related_name='licences')),
            ],
        ),
        migrations.CreateModel(
            name='Software',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('name', models.CharField(verbose_name='name', unique=True, max_length=255)),
                ('asset_type', models.PositiveSmallIntegerField(choices=[(1, 'back office'), (2, 'data center'), (3, 'part'), (4, 'all')], default=4)),
            ],
            options={
                'verbose_name_plural': 'software categories',
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
            field=models.ForeignKey(blank=True, to='assets.Manufacturer', on_delete=django.db.models.deletion.PROTECT, null=True),
        ),
        migrations.AddField(
            model_name='licence',
            name='office_infrastructure',
            field=models.ForeignKey(blank=True, to='back_office.OfficeInfrastructure', null=True),
        ),
        migrations.AddField(
            model_name='licence',
            name='property_of',
            field=models.ForeignKey(blank=True, to='assets.AssetHolder', on_delete=django.db.models.deletion.PROTECT, null=True),
        ),
        migrations.AddField(
            model_name='licence',
            name='region',
            field=models.ForeignKey(to='accounts.Region'),
        ),
        migrations.AddField(
            model_name='licence',
            name='software',
            field=models.ForeignKey(to='licences.Software', on_delete=django.db.models.deletion.PROTECT),
        ),
        migrations.AddField(
            model_name='licence',
            name='users',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL, related_name='_users_+', through='licences.LicenceUser'),
        ),
        migrations.AddField(
            model_name='baseobjectlicence',
            name='base_object',
            field=models.ForeignKey(to='assets.BaseObject', verbose_name='Asset', related_name='licences'),
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
