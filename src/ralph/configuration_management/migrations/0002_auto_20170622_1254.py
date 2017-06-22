# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import ralph.configuration_management.models
import dj.choices.fields


class Migration(migrations.Migration):

    dependencies = [
        ('configuration_management', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='scmstatuscheck',
            name='check_result',
            field=dj.choices.fields.ChoiceField(verbose_name='SCM check result', choices=ralph.configuration_management.models.SCMCheckResult),
        ),
    ]
