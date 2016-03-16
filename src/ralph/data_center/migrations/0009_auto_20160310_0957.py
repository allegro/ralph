# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_center', '0008_auto_20160308_0842'),
    ]

    database_operations = [
        migrations.AlterModelTable('NetworkKind', 'networks_networkkind'),
        migrations.AlterModelTable('NetworkEnvironment', 'networks_networkenvironment'),
        migrations.AlterModelTable('Network', 'networks_network'),
        migrations.AlterModelTable('NetworkTerminator', 'networks_networkterminator'),
        migrations.AlterModelTable('DiscoveryQueue', 'networks_discoveryqueue'),
        migrations.AlterModelTable('IPAddress', 'networks_ipaddress'),
    ]

    state_operations = [
        migrations.DeleteModel('NetworkKind'),
        migrations.DeleteModel('NetworkEnvironment'),
        migrations.DeleteModel('Network'),
        migrations.DeleteModel('NetworkTerminator'),
        migrations.DeleteModel('DiscoveryQueue'),
        migrations.DeleteModel('IPAddress'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=database_operations,
            state_operations=state_operations
        )
    ]
