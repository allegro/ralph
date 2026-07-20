from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('switchports', '0006_backendvalidationresult_raw_data'),
    ]

    operations = [
        migrations.AddField(
            model_name='rackswitchconfiguration',
            name='backend_validation',
            field=models.BooleanField(default=True, help_text='When enabled, netmaker backend validation is fetched and the netmaker column is shown for this switch in the switchport grid.'),
        ),
    ]
