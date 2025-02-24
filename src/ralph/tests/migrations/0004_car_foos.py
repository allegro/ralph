# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tests", "0003_bar"),
    ]

    operations = [
        migrations.AddField(
            model_name="car",
            name="foos",
            field=models.ManyToManyField(to="tests.Foo"),
        ),
    ]
