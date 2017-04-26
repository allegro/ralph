# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('polymorphic_tests', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SomeM2MModel',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('name', models.CharField(max_length=50)),
                ('polymorphics', models.ManyToManyField(to='polymorphic_tests.PolymorphicModelBaseTest', related_name='some_m2m')),
            ],
        ),
    ]
