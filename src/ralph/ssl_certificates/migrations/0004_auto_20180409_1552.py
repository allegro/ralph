# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ssl_certificates', '0003_sslcertificate_price'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sslcertificate',
            name='certificate_type',
            field=models.PositiveIntegerField(choices=[(1, 'EV'), (2, 'OV'), (3, 'DV'), (4, 'Wildcard'), (5, 'Multisan'), (6, 'CA ENT')], default=2),
        ),
    ]
