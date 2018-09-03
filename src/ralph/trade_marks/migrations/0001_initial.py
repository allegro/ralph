# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings
import ralph.lib.mixins.models


class Migration(migrations.Migration):

    dependencies = [
        ('domains', '0006_auto_20180725_1216'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('accounts', '0006_remove_ralphuser_gender'),
        ('assets', '0027_asset_buyout_date'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProviderAdditionalMarking',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255, verbose_name='name', unique=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='date created')),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='last modified')),
            ],
            options={
                'ordering': ['name'],
                'abstract': False,
            },
            bases=(ralph.lib.mixins.models.AdminAbsoluteUrlMixin, models.Model),
        ),
        migrations.CreateModel(
            name='TradeMarks',
            fields=[
                ('baseobject_ptr', models.OneToOneField(auto_created=True, primary_key=True, serialize=False, parent_link=True, to='assets.BaseObject')),
                ('registrant_number', models.CharField(max_length=255, verbose_name='Registrant number')),
                ('tm_type', models.PositiveIntegerField(default=2, choices=[(1, 'Word'), (2, 'Figurative'), (3, 'Word - Figurative')], verbose_name='Trade Mark type')),
                ('registrant_class', models.CharField(max_length=255, verbose_name='Registrant class')),
                ('date_to', models.DateField()),
                ('name', models.CharField(max_length=255, verbose_name='Trade Mark name')),
                ('order_number_url', models.URLField(null=True, max_length=255, blank=True)),
                ('tm_status', models.PositiveIntegerField(default=5, choices=[(1, 'Application filed'), (2, 'Application refused'), (3, 'Application withdrawn'), (4, 'Application opposed'), (5, 'Registered'), (6, 'Registration invalidated'), (7, 'Registration expired')], verbose_name='Trade Mark status')),
                ('additional_markings', models.ManyToManyField(to='trade_marks.ProviderAdditionalMarking')),
                ('business_owner', models.ForeignKey(related_name='trademark_business_owner', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
            bases=(ralph.lib.mixins.models.AdminAbsoluteUrlMixin, 'assets.baseobject', models.Model),
        ),
        migrations.CreateModel(
            name='TradeMarksLinkedDomains',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('domain', models.ForeignKey(related_name='tm_name', to='domains.Domain')),
                ('tm_name', models.ForeignKey(to='trade_marks.TradeMarks')),
            ],
        ),
        migrations.AddField(
            model_name='trademarks',
            name='domain',
            field=models.ManyToManyField(through='trade_marks.TradeMarksLinkedDomains', related_name='_trademarks_domain_+', to='domains.Domain'),
        ),
        migrations.AddField(
            model_name='trademarks',
            name='region',
            field=models.ForeignKey(to='accounts.Region'),
        ),
        migrations.AddField(
            model_name='trademarks',
            name='technical_owner',
            field=models.ForeignKey(related_name='trademark_technical_owner', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='trademarks',
            name='tm_holder',
            field=models.ForeignKey(blank=True, to='assets.AssetHolder', null=True, verbose_name='Trade Mark holder'),
        ),
        migrations.AlterUniqueTogether(
            name='trademarkslinkeddomains',
            unique_together=set([('tm_name', 'domain')]),
        ),
    ]
