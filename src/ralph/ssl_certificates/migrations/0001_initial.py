# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import ralph.lib.mixins.models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('assets', '0027_asset_buyout_date'),
    ]

    operations = [
        migrations.CreateModel(
            name='SSLCertificate',
            fields=[
                ('baseobject_ptr', models.OneToOneField(serialize=False, auto_created=True, parent_link=True, primary_key=True, to='assets.BaseObject')),
                ('name', models.CharField(verbose_name='certificate name', max_length=255, help_text='Full certificate name')),
                ('certificate_type', models.PositiveIntegerField(choices=[(1, 'EV'), (2, 'OV'), (3, 'DV'), (4, 'Wildcard'), (5, 'Multisan'), (6, 'CA ENT')], default=2)),
                ('date_from', models.DateField(null=True, blank=True)),
                ('date_to', models.DateField()),
                ('san', models.TextField(help_text='All Subject Alternative Name', blank=True)),
                ('price', models.DecimalField(null=True, default=0, decimal_places=2, max_digits=10, blank=True)),
                ('business_owner', models.ForeignKey(help_text='Business contact person for a certificate', related_name='certificates_business_owner', blank=True, null=True, to=settings.AUTH_USER_MODEL)),
                ('issued_by', models.ForeignKey(help_text='Company which receives certificate', blank=True, null=True, to='assets.AssetHolder')),
                ('technical_owner', models.ForeignKey(help_text='Technical contact person for a certificate', related_name='certificates_technical_owner', blank=True, null=True, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
            bases=(ralph.lib.mixins.models.AdminAbsoluteUrlMixin, 'assets.baseobject'),
        ),
    ]
