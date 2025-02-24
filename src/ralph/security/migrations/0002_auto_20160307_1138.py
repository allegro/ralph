# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations

import ralph.lib.mixins.models


class Migration(migrations.Migration):
    dependencies = [
        ("security", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="securityscan",
            name="tags",
            field=ralph.lib.mixins.models.TaggableManager(
                blank=True,
                verbose_name="Tags",
                help_text="A comma-separated list of tags.",
                to="taggit.Tag",
                through="taggit.TaggedItem",
            ),
        ),
        migrations.AlterField(
            model_name="vulnerability",
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
