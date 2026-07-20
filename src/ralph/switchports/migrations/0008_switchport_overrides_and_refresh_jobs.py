import django.db.models.deletion
from django.db import migrations, models

import ralph.lib.mixins.models


class Migration(migrations.Migration):

    dependencies = [
        ('data_center', '0041_alter_accessory_id_alter_baseobjectcluster_id_and_more'),
        ('switchports', '0007_rackswitchconfiguration_backend_validation'),
    ]

    operations = [
        migrations.CreateModel(
            name='RackSwitchConfigurationOverride',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data_center_asset', models.ForeignKey(help_text='The server whose connection deviates from the column default.', on_delete=django.db.models.deletion.CASCADE, related_name='+', to='data_center.datacenterasset')),
                ('rack_switch_configuration', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='overrides', to='switchports.rackswitchconfiguration')),
                ('switch', models.ForeignKey(help_text='The alternate switch this server connects to for this column.', on_delete=django.db.models.deletion.CASCADE, related_name='+', to='data_center.datacenterasset')),
            ],
            options={
                'unique_together': {('rack_switch_configuration', 'data_center_asset')},
            },
            bases=(ralph.lib.mixins.models.AdminAbsoluteUrlMixin, models.Model),
        ),
        migrations.CreateModel(
            name='SwitchportRefreshJob',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='date created')),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='last modified')),
                ('status', models.CharField(choices=[('PENDING', 'Pending'), ('IN_PROGRESS', 'In progress'), ('SUCCESS', 'Success'), ('ERROR', 'Error')], db_index=True, default='PENDING', max_length=20)),
                ('started_at', models.DateTimeField(blank=True, null=True)),
                ('finished_at', models.DateTimeField(blank=True, null=True)),
                ('summary', models.JSONField(blank=True, help_text='Per-switch counts and errors collected during the refresh.', null=True)),
                ('error', models.TextField(blank=True, default='')),
                ('rack_configuration', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='refresh_jobs', to='switchports.rackconfiguration')),
            ],
            options={
                'ordering': ('-created',),
            },
            bases=(ralph.lib.mixins.models.AdminAbsoluteUrlMixin, ralph.lib.mixins.models.TimeStampMixin, models.Model),
        ),
    ]
