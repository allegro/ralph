# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def populate_ok_field(apps, schema_editor):
    SCMStatusCheck = apps.get_model("configuration_management", "SCMStatusCheck")
    SCMStatusCheck.objects.filter(check_result=1).update(ok=True)


class Migration(migrations.Migration):
    dependencies = [
        ("configuration_management", "0002_auto_20170622_1254"),
    ]

    operations = [
        migrations.AddField(
            model_name="scmstatuscheck",
            name="ok",
            field=models.BooleanField(editable=False, default=False),
        ),
        migrations.RunPython(populate_ok_field, reverse_code=migrations.RunPython.noop),
    ]
