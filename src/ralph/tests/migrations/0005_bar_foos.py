# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tests", "0004_car_foos"),
    ]

    operations = [
        migrations.AddField(
            model_name="bar",
            name="foos",
            field=models.ManyToManyField(
                blank=True, to="tests.Foo", related_name="bars"
            ),
        ),
    ]
