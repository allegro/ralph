# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from dateutil.relativedelta import relativedelta
from django.db import migrations, models


def get_depreciation_months(asset):
    return int(
        (1 / (asset.depreciation_rate / 100) * 12) if asset.depreciation_rate else 0
    )


def calculate_buyout_date(asset):
    if asset.depreciation_end_date:
        return asset.depreciation_end_date
    elif asset.invoice_date:
        return asset.invoice_date + relativedelta(
            months=get_depreciation_months(asset) + 1
        )
    else:
        return None


def update_buyout_date(apps, schema_editor):
    Asset = apps.get_model("assets", "Asset")
    for asset in Asset.objects.filter(model__category__show_buyout_date=True):
        asset.buyout_date = calculate_buyout_date(asset)
        asset.save(update_fields=["buyout_date"])


class Migration(migrations.Migration):
    dependencies = [
        ("assets", "0026_auto_20170510_0840"),
    ]

    operations = [
        migrations.AddField(
            model_name="asset",
            name="buyout_date",
            field=models.DateField(blank=True, db_index=True, null=True),
        ),
        migrations.RunPython(
            update_buyout_date, reverse_code=migrations.RunPython.noop
        ),
    ]
