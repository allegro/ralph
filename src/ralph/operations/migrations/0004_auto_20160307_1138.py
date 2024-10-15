# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import ralph.lib.mixins.models


class Migration(migrations.Migration):

    dependencies = [
        ("operations", "0003_auto_20160303_1114"),
    ]

    operations = [
        migrations.AlterField(
            model_name="operation",
            name="tags",
            field=ralph.lib.mixins.models.TaggableManager(
                blank=True,
                verbose_name="Tags",
                help_text="A comma-separated list of tags.",
                to="taggit.Tag",
                through="taggit.TaggedItem",
            ),
        ),
    ]
