# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("data_center", "0022_auto_20161206_1521"),
    ]

    operations = [
        migrations.AddField(
            model_name="rack",
            name="reverse_ordering",
            field=models.BooleanField(
                help_text=(
                    "Check if RU numbers count from top to bottom with "
                    "position 1 starting at the top of the rack. If "
                    "unchecked position 1 is at the bottom of the rack"
                ),
                default=settings.RACK_LISTING_NUMBERING_TOP_TO_BOTTOM,
                verbose_name="RU order top to bottom",
            ),
        ),
    ]
