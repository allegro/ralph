# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings
import ralph.lib.mixins.models


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0027_asset_buyout_date'),
        ('domains', '0006_auto_20180725_1216'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('accounts', '0006_remove_ralphuser_gender'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProviderAdditionalMarking',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('name', models.CharField(max_length=255, unique=True, verbose_name='name')),
                ('created', models.DateTimeField(verbose_name='date created', auto_now_add=True)),
                ('modified', models.DateTimeField(verbose_name='last modified', auto_now=True)),
            ],
            options={
                'ordering': ['name'],
                'abstract': False,
            },
            bases=(ralph.lib.mixins.models.AdminAbsoluteUrlMixin, models.Model),
        ),
        migrations.CreateModel(
            name='TradeMark',
            fields=[
                ('baseobject_ptr', models.OneToOneField(to='assets.BaseObject', primary_key=True, parent_link=True, serialize=False, auto_created=True)),
                ('name', models.CharField(max_length=255, verbose_name='Trade Mark name')),
                ('registrant_number', models.CharField(max_length=255, verbose_name='Registrant number')),
                ('type', models.PositiveIntegerField(choices=[(1, 'Word'), (2, 'Figurative'), (3, 'Word - Figurative')], verbose_name='Trade Mark type', default=2)),
                ('registrant_class', models.CharField(max_length=255, verbose_name='Registrant class')),
                ('valid_to', models.DateField()),
                ('order_number_url', models.URLField(max_length=255, blank=True, null=True)),
                ('status', models.PositiveIntegerField(choices=[(1, 'Application filed'), (2, 'Application refused'), (3, 'Application withdrawn'), (4, 'Application opposed'), (5, 'Registered'), (6, 'Registration invalidated'), (7, 'Registration expired')], verbose_name='Trade Mark status', default=5)),
                ('additional_markings', models.ManyToManyField(blank=True, to='trade_marks.ProviderAdditionalMarking')),
                ('business_owner', models.ForeignKey(to=settings.AUTH_USER_MODEL, related_name='trademark_business_owner')),
            ],
            options={
                'abstract': False,
            },
            bases=(ralph.lib.mixins.models.AdminAbsoluteUrlMixin, 'assets.baseobject', models.Model),
        ),
        migrations.CreateModel(
            name='TradeMarksLinkedDomain',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('domain', models.ForeignKey(to='domains.Domain', related_name='trade_mark')),
                ('trade_mark', models.ForeignKey(to='trade_marks.TradeMark')),
            ],
        ),
        migrations.AddField(
            model_name='trademark',
            name='domains',
            field=models.ManyToManyField(through='trade_marks.TradeMarksLinkedDomain', to='domains.Domain', related_name='_trademark_domains_+'),
        ),
        migrations.AddField(
            model_name='trademark',
            name='holder',
            field=models.ForeignKey(blank=True, null=True, verbose_name='Trade Mark holder', to='assets.AssetHolder'),
        ),
        migrations.AddField(
            model_name='trademark',
            name='region',
            field=models.ForeignKey(to='accounts.Region'),
        ),
        migrations.AddField(
            model_name='trademark',
            name='technical_owner',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, related_name='trademark_technical_owner'),
        ),
        migrations.AlterUniqueTogether(
            name='trademarkslinkeddomain',
            unique_together=set([('trade_mark', 'domain')]),
        ),
    ]
