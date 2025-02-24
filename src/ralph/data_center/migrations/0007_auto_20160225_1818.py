# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("supports", "0005_auto_20160105_1222"),
        ("assets", "0008_auto_20160122_1429"),
        ("licences", "0002_auto_20151204_1325"),
        ("data_center", "0006_rack_require_position"),
    ]

    # move models to virtual app
    database_operations = [
        migrations.AlterModelTable("VirtualServer", "virtual_virtualserver"),
        migrations.AlterModelTable("CloudProject", "virtual_cloudproject"),
    ]

    state_operations = [
        migrations.DeleteModel("VirtualServer"),
        migrations.DeleteModel("CloudProject"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=database_operations, state_operations=state_operations
        )
    ]
