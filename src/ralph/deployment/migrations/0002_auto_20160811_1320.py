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
            field=models.TextField(verbose_name='configuration', help_text='All newline characters will be converted to Unix \\n newlines.\nYou can use {{variables}} in the body.\nAvailable variables:\n<br>    - configuration_path,\n<br>    - dc,\n<br>    - deployment_id,\n<br>    - domain,\n<br>    - done_url,\n<br>    - hostname,\n<br>    - initrd,\n<br>    - kernel,\n<br>    - kickstart,\n<br>    - ralph_instance,\n<br>    - service_env,', blank=True),
        ),
    ]
