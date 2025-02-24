# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("trade_marks", "0001_initial"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="trademarkslinkeddomains",
            options={
                "verbose_name": "Trade Marks Linked Domain",
                "verbose_name_plural": "Trade Marks Linked Domains",
            },
        ),
    ]
