# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("assets", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="assetholder",
            name="created",
            field=models.DateTimeField(auto_now_add=True, verbose_name="date created"),
        ),
        migrations.AlterField(
            model_name="assetholder",
            name="modified",
            field=models.DateTimeField(auto_now=True, verbose_name="last modified"),
        ),
        migrations.AlterField(
            model_name="assetmodel",
            name="created",
            field=models.DateTimeField(auto_now_add=True, verbose_name="date created"),
        ),
        migrations.AlterField(
            model_name="assetmodel",
            name="modified",
            field=models.DateTimeField(auto_now=True, verbose_name="last modified"),
        ),
        migrations.AlterField(
            model_name="baseobject",
            name="created",
            field=models.DateTimeField(auto_now_add=True, verbose_name="date created"),
        ),
        migrations.AlterField(
            model_name="baseobject",
            name="modified",
            field=models.DateTimeField(auto_now=True, verbose_name="last modified"),
        ),
        migrations.AlterField(
            model_name="budgetinfo",
            name="created",
            field=models.DateTimeField(auto_now_add=True, verbose_name="date created"),
        ),
        migrations.AlterField(
            model_name="budgetinfo",
            name="modified",
            field=models.DateTimeField(auto_now=True, verbose_name="last modified"),
        ),
        migrations.AlterField(
            model_name="category",
            name="created",
            field=models.DateTimeField(auto_now_add=True, verbose_name="date created"),
        ),
        migrations.AlterField(
            model_name="category",
            name="modified",
            field=models.DateTimeField(auto_now=True, verbose_name="last modified"),
        ),
        migrations.AlterField(
            model_name="environment",
            name="created",
            field=models.DateTimeField(auto_now_add=True, verbose_name="date created"),
        ),
        migrations.AlterField(
            model_name="environment",
            name="modified",
            field=models.DateTimeField(auto_now=True, verbose_name="last modified"),
        ),
        migrations.AlterField(
            model_name="manufacturer",
            name="created",
            field=models.DateTimeField(auto_now_add=True, verbose_name="date created"),
        ),
        migrations.AlterField(
            model_name="manufacturer",
            name="modified",
            field=models.DateTimeField(auto_now=True, verbose_name="last modified"),
        ),
        migrations.AlterField(
            model_name="service",
            name="created",
            field=models.DateTimeField(auto_now_add=True, verbose_name="date created"),
        ),
        migrations.AlterField(
            model_name="service",
            name="modified",
            field=models.DateTimeField(auto_now=True, verbose_name="last modified"),
        ),
    ]
