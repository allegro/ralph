# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('custom_fields', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='customfield',
            name='use_as_configuration_variable',
            field=models.BooleanField(default=False, help_text='When set, this variable will be exposed in API in "configuration_variables" section. You could use this later in configuration management tool like Puppet or Ansible.'),
        ),
    ]
