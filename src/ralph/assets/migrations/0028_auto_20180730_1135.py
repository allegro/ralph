# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django
from django.db import migrations, models


def rewrite_business_segment_from_pc(apps, schema_editor):
    Service = apps.get_model("assets", "Service")
    for service in Service.objects.filter(
        profit_center__business_segment__isnull=False
    ):
        print(
            "Assigning {} to {}".format(
                service.profit_center.business_segment.name, service.name
            )
        )
        service.business_segment = service.profit_center.business_segment
        service.save(update_fields=["business_segment"])


def rewrite_business_segment_to_pc(apps, schema_editor):
    Service = apps.get_model("assets", "Service")
    for service in Service.objects.filter(
        profit_center__isnull=False, business_segment__isnull=False
    ):
        print(
            "Assigning {} to {}".format(
                service.business_segment.name, service.profit_center.name
            )
        )
        service.profit_center.business_segment = service.business_segment
        service.profit_center.save(update_fields=["business_segment"])


class Migration(migrations.Migration):
    dependencies = [
        ("assets", "0027_asset_buyout_date"),
    ]

    operations = [
        migrations.AddField(
            model_name="service",
            name="business_segment",
            field=models.ForeignKey(
                blank=True,
                null=True,
                to="assets.BusinessSegment",
                on_delete=django.db.models.deletion.CASCADE,
            ),
        ),
        migrations.RunPython(
            rewrite_business_segment_from_pc,
            reverse_code=rewrite_business_segment_to_pc,
        ),
        migrations.RemoveField(
            model_name="profitcenter",
            name="business_segment",
        ),
    ]
