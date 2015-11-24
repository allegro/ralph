# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings
import ralph.lib.mixins.models


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Domain',
            fields=[
                ('baseobject_ptr', models.OneToOneField(auto_created=True, to='assets.BaseObject', parent_link=True, serialize=False, primary_key=True)),
                ('name', models.CharField(unique=True, verbose_name='Domain name', help_text='Full domain name', max_length=255)),
                ('domain_status', models.PositiveIntegerField(choices=[(1, 'Active'), (2, 'Pending lapse'), (3, 'Pending transfer away'), (4, 'Lapsed (inactive)'), (5, 'Transfered away')], default=1)),
                ('business_owner', models.ForeignKey(to=settings.AUTH_USER_MODEL, null=True, related_name='domaincontract_business_owner', help_text='Business contact person for a domain', blank=True)),
                ('business_segment', models.ForeignKey(null=True, to='assets.BusinessSegment', help_text='Business segment for a domain', blank=True)),
                ('domain_holder', models.ForeignKey(null=True, to='assets.AssetHolder', help_text='Company which receives invoice for the domain', blank=True)),
                ('technical_owner', models.ForeignKey(to=settings.AUTH_USER_MODEL, null=True, related_name='domaincontract_technical_owner', help_text='Technical contact person for a domain', blank=True)),
            ],
            options={
                'abstract': False,
            },
            bases=('assets.baseobject', ralph.lib.mixins.models.AdminAbsoluteUrlMixin),
        ),
        migrations.CreateModel(
            name='DomainContract',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('created', models.DateTimeField(verbose_name='date created', auto_now=True)),
                ('modified', models.DateTimeField(auto_now_add=True, verbose_name='last modified')),
                ('expiration_date', models.DateField(null=True, blank=True)),
                ('price', models.DecimalField(decimal_places=2, null=True, verbose_name='Price', help_text='Price for domain renewal for given period', max_digits=15, blank=True)),
                ('domain', models.ForeignKey(to='domains.Domain')),
            ],
            options={
                'abstract': False,
            },
            bases=(ralph.lib.mixins.models.AdminAbsoluteUrlMixin, models.Model),
        ),
        migrations.CreateModel(
            name='DomainRegistrant',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('name', models.CharField(verbose_name='name', max_length=255, unique=True)),
                ('created', models.DateTimeField(verbose_name='date created', auto_now=True)),
                ('modified', models.DateTimeField(auto_now_add=True, verbose_name='last modified')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='domaincontract',
            name='registrant',
            field=models.ForeignKey(null=True, to='domains.DomainRegistrant', blank=True),
        ),
    ]
