# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ssl_certificates', '0002_sslcertificate_domain_ssl'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sslcertificate',
            name='issued_by',
            field=models.ForeignKey(blank=True, to='assets.AssetHolder', help_text='Company which delivered certificate', null=True),
        ),
        migrations.AlterField(
            model_name='sslcertificate',
            name='san',
            field=models.TextField(blank=True, help_text='All Subject Alternative Names'),
        ),
    ]
