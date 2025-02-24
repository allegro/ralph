# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("supports", "0003_auto_20151204_1325"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="BaseObjectsSupport",
            unique_together=set([("support", "baseobject")]),
        ),
    ]
