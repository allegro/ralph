# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("assets", "0006_category_show_buyout_date"),
    ]

    operations = [
        migrations.AlterField(
            model_name="assetmodel",
            name="visualization_layout_back",
            field=models.PositiveIntegerField(
                verbose_name="visualization layout of back side",
                choices=[
                    (1, "N/A"),
                    (2, "1 row x 2 columns"),
                    (3, "2 rows x 8 columns"),
                    (4, "2 rows x 16 columns (A/B)"),
                    (5, "4 rows x 2 columns"),
                    (6, "2 rows x 4 columns"),
                    (7, "2 rows x 2 columns"),
                    (8, "1 rows x 14 columns"),
                    (9, "2 rows x 1 columns"),
                ],
                default=1,
                blank=True,
            ),
        ),
        migrations.AlterField(
            model_name="assetmodel",
            name="visualization_layout_front",
            field=models.PositiveIntegerField(
                verbose_name="visualization layout of front side",
                choices=[
                    (1, "N/A"),
                    (2, "1 row x 2 columns"),
                    (3, "2 rows x 8 columns"),
                    (4, "2 rows x 16 columns (A/B)"),
                    (5, "4 rows x 2 columns"),
                    (6, "2 rows x 4 columns"),
                    (7, "2 rows x 2 columns"),
                    (8, "1 rows x 14 columns"),
                    (9, "2 rows x 1 columns"),
                ],
                default=1,
                blank=True,
            ),
        ),
    ]
