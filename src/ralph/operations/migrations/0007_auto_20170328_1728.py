# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("operations", "0006_auto_20170323_1530"),
    ]

    operations = [
        migrations.RenameField(
            model_name="operation", old_name="asignee", new_name="assignee"
        )
    ]
