# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings
import ralph.lib.mixins.models


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0027_asset_buyout_date'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='SSLCertificate',
            fields=[
                ('baseobject_ptr', models.OneToOneField(to='assets.BaseObject', parent_link=True, primary_key=True, auto_created=True, serialize=False)),
                ('certificate', models.CharField(help_text='Full certificate name and type', verbose_name='certificate name', max_length=255)),
                ('valid_thru', models.DateField(null=True, blank=True)),
                ('business_owner', models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL, help_text='Business contact person for a certificate', blank=True, related_name='certificates_business_owner')),
                ('certificate_holder', models.ForeignKey(null=True, to='assets.AssetHolder', help_text='Company which receives invoice for certificate', blank=True)),
                ('technical_owner', models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL, help_text='Technical contact person for a certificate', blank=True, related_name='certificates_technical_owner')),
            ],
            options={
                'abstract': False,
            },
            bases=(ralph.lib.mixins.models.AdminAbsoluteUrlMixin, 'assets.baseobject'),
        ),
        migrations.CreateModel(
            name='SSLCertificateContract',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('created', models.DateTimeField(verbose_name='date created', auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='last modified')),
                ('price', models.DecimalField(null=True, max_digits=15, decimal_places=2, blank=True, help_text='Price for SSL Certificate for given period', verbose_name='Price')),
                ('certificate', models.ForeignKey(to='ssl_certificates.SSLCertificate')),
            ],
            options={
                'abstract': False,
            },
            bases=(ralph.lib.mixins.models.AdminAbsoluteUrlMixin, models.Model),
        ),
    ]
