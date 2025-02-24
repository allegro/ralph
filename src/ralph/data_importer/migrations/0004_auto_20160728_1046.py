# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("data_importer", "0003_auto_20160624_1217"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="importedobjects",
            unique_together=set(
                [("content_type", "object_pk"), ("content_type", "old_object_pk")]
            ),
        ),
    ]
