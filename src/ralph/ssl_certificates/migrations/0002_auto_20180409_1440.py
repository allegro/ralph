# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0027_asset_buyout_date'),
        ('ssl_certificates', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='sslcertificate',
            name='certificate_holder',
        ),
        migrations.AddField(
            model_name='sslcertificate',
            name='certificate_issued_by',
            field=models.ForeignKey(help_text='Company which receives certificate', to='assets.AssetHolder', null=True, blank=True),
        ),
        migrations.AddField(
            model_name='sslcertificate',
            name='certificate_type',
            field=models.PositiveIntegerField(default=2, choices=[(1, 'EV'), (2, 'OV'), (3, 'DV'), (4, 'Wildcard'), (5, 'Multisan')]),
        ),
        migrations.AddField(
            model_name='sslcertificate',
            name='san',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='sslcertificate',
            name='certificate',
            field=models.CharField(help_text='Full certificate name', verbose_name='certificate name', max_length=255),
        ),
    ]
