# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("reports", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="report",
            name="created",
            field=models.DateTimeField(auto_now_add=True, verbose_name="date created"),
        ),
        migrations.AlterField(
            model_name="report",
            name="modified",
            field=models.DateTimeField(auto_now=True, verbose_name="last modified"),
        ),
        migrations.AlterField(
            model_name="reportlanguage",
            name="created",
            field=models.DateTimeField(auto_now_add=True, verbose_name="date created"),
        ),
        migrations.AlterField(
            model_name="reportlanguage",
            name="modified",
            field=models.DateTimeField(auto_now=True, verbose_name="last modified"),
        ),
        migrations.AlterField(
            model_name="reporttemplate",
            name="created",
            field=models.DateTimeField(auto_now_add=True, verbose_name="date created"),
        ),
        migrations.AlterField(
            model_name="reporttemplate",
            name="modified",
            field=models.DateTimeField(auto_now=True, verbose_name="last modified"),
        ),
    ]
