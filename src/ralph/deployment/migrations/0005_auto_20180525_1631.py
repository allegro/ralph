# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('deployment', '0004_auto_20161128_1359'),
    ]

    operations = [
        migrations.AlterField(
            model_name='prebootconfiguration',
            name='configuration',
            field=models.TextField(help_text="All newline characters will be converted to Unix \\n newlines.\n<br>You can use {{variables}} in the body.\n<br>Available variables:\n\n<br>  - configuration_class_name (eg. 'www')\n<br>  - configuration_module (eg. 'ralph')\n<br>  - configuration_path (eg. 'ralph/www')\n<br>  - dc (eg. 'data-center1')\n<br>  - deployment_id (eg. 'ea9ea3a0-1c4d-42b7-a19b-922000abe9f7')\n<br>  - domain (eg. 'dc1.mydc.net')\n<br>  - done_url (eg. 'http://ralph.example.com/deployment/ea9ea3a0-1c4d-42b7-a19b-922000abe9f7/mark_as_done')\n<br>  - hostname (eg. 'ralph123.dc1.mydc.net')\n<br>  - initrd (eg. 'http://ralph.example.com/deployment/ea9ea3a0-1c4d-42b7-a19b-922000abe9f7/initrd')\n<br>  - kernel (eg. 'http://ralph.example.com/deployment/ea9ea3a0-1c4d-42b7-a19b-922000abe9f7/kernel')\n<br>  - netboot (eg. 'http://ralph.example.com/deployment/ea9ea3a0-1c4d-42b7-a19b-922000abe9f7/netboot')\n<br>  - kickstart (eg. 'http://ralph.example.com/deployment/ea9ea3a0-1c4d-42b7-a19b-922000abe9f7/kickstart')\n<br>  - preseed (eg. 'http://ralph.example.com/deployment/ea9ea3a0-1c4d-42b7-a19b-922000abe9f7/preseed')\n<br>  - script (eg. 'http://ralph.example.com/deployment/ea9ea3a0-1c4d-42b7-a19b-922000abe9f7/script')\n<br>  - ralph_instance (eg. 'http://ralph.example.com')\n<br>  - service_env (eg. 'Backup systems - prod')\n<br>  - service_uid (eg. 'sc-123')", blank=True, verbose_name='configuration'),
        ),
    ]
