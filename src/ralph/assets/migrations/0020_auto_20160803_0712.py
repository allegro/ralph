# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations

from ralph.assets._migration_helpers import InheritFromBaseObject


class Migration(migrations.Migration):
    dependencies = [
        ("assets", "0019_auto_20160719_1443"),
        ("data_importer", "0004_auto_20160728_1046"),
    ]

    operations = [
        InheritFromBaseObject(
            "assets",
            "ConfigurationClass",
            rewrite_fields={
                "created": "created",
                "modified": "modified",
            },
        ),
        migrations.RemoveField(
            model_name="configurationclass",
            name="created",
        ),
        migrations.RemoveField(
            model_name="configurationclass",
            name="modified",
        ),
    ]
