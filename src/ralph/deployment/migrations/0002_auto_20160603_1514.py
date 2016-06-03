# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('deployment', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='prebootconfiguration',
            name='configuration',
            field=models.TextField(help_text='All newline characters will be converted to Unix \\n newlines. You can use {{variables}} in the body. Available variables: ralph_instance, deployment_id, kickstart, initrd, kernel, dc, done_url.', blank=True, verbose_name='configuration'),
        ),
    ]
