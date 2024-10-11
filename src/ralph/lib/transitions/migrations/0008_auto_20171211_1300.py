# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transitions', '0007_transition_template_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transitionjob',
            name='transition',
            field=models.ForeignKey(to='transitions.Transition', related_name='jobs', on_delete=django.db.models.deletion.CASCADE),
        ),
    ]
