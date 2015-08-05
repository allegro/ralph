# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('back_office', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='backofficeasset',
            options={'verbose_name': 'Back Office Asset', 'verbose_name_plural': 'Back Office Assets'},
        ),
        migrations.AddField(
            model_name='backofficeasset',
            name='loan_end_date',
            field=models.DateField(default=None, verbose_name='Loan end date', blank=True, null=True),
        ),
        migrations.AddField(
            model_name='backofficeasset',
            name='purchase_order',
            field=models.CharField(max_length=50, null=True, blank=True),
        ),
    ]
