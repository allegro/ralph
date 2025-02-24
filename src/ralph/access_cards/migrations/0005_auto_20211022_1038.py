# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations

from ralph.lib.transitions.migration import TransitionActionMigration


class Migration(migrations.Migration):
    dependencies = [
        ("access_cards", "0004_auto_20200513_1014"),
    ]

    operations = [TransitionActionMigration()]
