# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("dhcp", "0005_change_related_name"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="dnsserver",
            name="is_default",
        ),
    ]
