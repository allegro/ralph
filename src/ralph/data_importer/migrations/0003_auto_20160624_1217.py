# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("data_importer", "0002_auto_20151125_1354"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="importedobjects",
            options={},
        ),
        migrations.AlterUniqueTogether(
            name="importedobjects",
            unique_together=set([("content_type", "object_pk", "old_object_pk")]),
        ),
    ]
