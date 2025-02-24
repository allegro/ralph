# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("assets", "0023_category_allow_deployment"),
    ]

    operations = [
        migrations.AlterField(
            model_name="baseobject",
            name="configuration_path",
            field=models.ForeignKey(
                verbose_name="configuration path",
                blank=True,
                help_text="path to configuration for this object, for example path to puppet class",
                on_delete=django.db.models.deletion.PROTECT,
                null=True,
                to="assets.ConfigurationClass",
            ),
        ),
        migrations.AlterField(
            model_name="baseobject",
            name="parent",
            field=models.ForeignKey(
                related_name="children",
                to="assets.BaseObject",
                blank=True,
                on_delete=django.db.models.deletion.SET_NULL,
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="baseobject",
            name="service_env",
            field=models.ForeignKey(
                to="assets.ServiceEnvironment",
                on_delete=django.db.models.deletion.PROTECT,
                null=True,
            ),
        ),
    ]
