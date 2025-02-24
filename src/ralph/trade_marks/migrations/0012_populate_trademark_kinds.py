# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def populate_trademark_kinds(apps, schema_editor):
    TradeMarkKind = apps.get_model("trade_marks", "TradeMarkKind")

    TradeMarkKind(
        id=1,
        type="Word",
    ).save()

    TradeMarkKind(
        id=2,
        type="Figurative",
    ).save()

    TradeMarkKind(
        id=3,
        type="Word - Figurative",
    ).save()

    TradeMarkKind(
        id=4,
        type="3D",
    ).save()


class Migration(migrations.Migration):
    dependencies = [
        ("trade_marks", "0011_trademarkkind"),
    ]

    operations = [
        migrations.RunPython(
            populate_trademark_kinds, reverse_code=migrations.RunPython.noop
        ),
    ]
