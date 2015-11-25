# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import ralph.lib.mixins.models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0006_auto_20151110_1448'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Domain',
            fields=[
                ('baseobject_ptr', models.OneToOneField(primary_key=True, auto_created=True, to='assets.BaseObject', parent_link=True, serialize=False)),
                ('name', models.CharField(max_length=255, help_text='Full domain name', verbose_name='Domain name', unique=True)),
                ('domain_status', models.PositiveIntegerField(default=1, choices=[(1, 'Active'), (2, 'Pending lapse'), (3, 'Pending transfer away'), (4, 'Lapsed (inactive)'), (5, 'Transfered away')])),
                ('business_owner', models.ForeignKey(null=True, blank=True, related_name='domaincontract_business_owner', to=settings.AUTH_USER_MODEL, help_text='Business contact person for a domain')),
                ('business_segment', models.ForeignKey(null=True, blank=True, to='assets.BusinessSegment', help_text='Business segment for a domain')),
                ('domain_holder', models.ForeignKey(null=True, blank=True, to='assets.AssetHolder', help_text='Company which receives invoice for the domain')),
                ('technical_owner', models.ForeignKey(null=True, blank=True, related_name='domaincontract_technical_owner', to=settings.AUTH_USER_MODEL, help_text='Technical contact person for a domain')),
            ],
            options={
                'abstract': False,
            },
            bases=('assets.baseobject', ralph.lib.mixins.models.AdminAbsoluteUrlMixin),
        ),
        migrations.CreateModel(
            name='DomainContract',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, primary_key=True, verbose_name='ID')),
                ('created', models.DateTimeField(verbose_name='date created', auto_now=True)),
                ('modified', models.DateTimeField(auto_now_add=True, verbose_name='last modified')),
                ('expiration_date', models.DateField(null=True, blank=True)),
                ('price', models.DecimalField(decimal_places=2, null=True, blank=True, max_digits=15, help_text='Price for domain renewal for given period', verbose_name='Price')),
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
                ('id', models.AutoField(auto_created=True, serialize=False, primary_key=True, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='name', unique=True)),
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
            field=models.ForeignKey(null=True, blank=True, to='domains.DomainRegistrant'),
        ),
    ]
