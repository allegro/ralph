# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("data_center", "0020_auto_20160907_1116"),
    ]

    operations = [
        migrations.AlterField(
            model_name="serverroom",
            name="visualization_cols_num",
            field=models.PositiveIntegerField(
                default=20,
                verbose_name="visualization grid columns number",
                validators=[
                    django.core.validators.MinValueValidator(1),
                    django.core.validators.MaxValueValidator(100),
                ],
            ),
        ),
        migrations.AlterField(
            model_name="serverroom",
            name="visualization_rows_num",
            field=models.PositiveIntegerField(
                default=20,
                verbose_name="visualization grid rows number",
                validators=[
                    django.core.validators.MinValueValidator(1),
                    django.core.validators.MaxValueValidator(100),
                ],
            ),
        ),
    ]
