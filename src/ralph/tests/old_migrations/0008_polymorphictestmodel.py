# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0019_auto_20160525_1113'),
        ('tests', '0007_order_remarks'),
    ]

    operations = [
        migrations.CreateModel(
            name='PolymorphicTestModel',
            fields=[
                ('baseobject_ptr', models.OneToOneField(serialize=False, auto_created=True, primary_key=True, to='assets.BaseObject', parent_link=True)),
                ('hostname', models.CharField(max_length=50)),
            ],
            options={
                'abstract': False,
            },
            bases=('assets.baseobject',),
        ),
    ]
