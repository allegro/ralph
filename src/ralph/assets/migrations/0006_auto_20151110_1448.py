# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0005_assetholder'),
    ]

    operations = [
        migrations.CreateModel(
            name='BudgetInfo',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('name', models.CharField(verbose_name='name', max_length=255, unique=True)),
                ('created', models.DateTimeField(verbose_name='date created', auto_now=True)),
                ('modified', models.DateTimeField(verbose_name='last modified', auto_now_add=True)),
            ],
            options={
                'verbose_name_plural': 'Budgets info',
                'verbose_name': 'Budget info',
            },
        ),
        migrations.AddField(
            model_name='asset',
            name='budget_info',
            field=models.ForeignKey(null=True, to='assets.BudgetInfo', blank=True, on_delete=django.db.models.deletion.PROTECT, default=None),
        ),
    ]
