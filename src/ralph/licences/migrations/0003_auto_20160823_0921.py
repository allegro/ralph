# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("licences", "0002_auto_20151204_1325"),
    ]

    operations = [
        migrations.AlterField(
            model_name="licence",
            name="base_objects",
            field=models.ManyToManyField(
                to="assets.BaseObject",
                through="licences.BaseObjectLicence",
                verbose_name="assigned base objects",
                related_name="_licence_base_objects_+",
            ),
        ),
        migrations.AlterField(
            model_name="licence",
            name="invoice_date",
            field=models.DateField(null=True, blank=True, verbose_name="invoice date"),
        ),
        migrations.AlterField(
            model_name="licence",
            name="license_details",
            field=models.CharField(
                blank=True, verbose_name="license details", default="", max_length=1024
            ),
        ),
        migrations.AlterField(
            model_name="licence",
            name="niw",
            field=models.CharField(
                unique=True,
                verbose_name="inventory number",
                default="N/A",
                max_length=200,
            ),
        ),
        migrations.AlterField(
            model_name="licence",
            name="number_bought",
            field=models.IntegerField(verbose_name="number of purchased items"),
        ),
        migrations.AlterField(
            model_name="licence",
            name="sn",
            field=models.TextField(null=True, blank=True, verbose_name="SN / key"),
        ),
    ]
