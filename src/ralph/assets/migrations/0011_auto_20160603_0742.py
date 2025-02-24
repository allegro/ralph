# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations

import ralph.lib.mixins.fields


def migrate_hostname(apps, schema_editor):
    Asset = apps.get_model("assets", "Asset")
    # update all assets where hostname is empty string to null hostname
    Asset.objects.filter(hostname="").update(hostname=None)


def rev_migrate_hostname(apps, schema_editor):
    Asset = apps.get_model("assets", "Asset")
    Asset.objects.filter(hostname__isnull=True).update(hostname="")


class Migration(migrations.Migration):
    dependencies = [
        ("assets", "0010_auto_20160405_1531"),
    ]

    operations = [
        migrations.RunPython(
            migrate_hostname,
            # this reverse has te be executed after altering field back to
            # CharField in reverse migration to use `CharField.to_python`
            # (to get '') instead of `NullableCharField.to_python`
            # (which returns None)
            rev_migrate_hostname,
        ),
        migrations.AlterField(
            model_name="asset",
            name="hostname",
            field=ralph.lib.mixins.fields.NullableCharField(
                default=None,
                max_length=255,
                blank=True,
                null=True,
                verbose_name="hostname",
            ),
        ),
    ]
