from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('switchports', '0004_alter_rackswitchconfiguration_label_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='backendvalidationresult',
            name='oper_status',
            field=models.CharField(blank=True, default='', help_text='Operational status reported by the backend (up/down/unknown)', max_length=20),
        ),
        migrations.AddField(
            model_name='backendvalidationresult',
            name='admin_status',
            field=models.CharField(blank=True, default='', help_text='Administrative status reported by the backend (up/down/unknown)', max_length=20),
        ),
        migrations.AddField(
            model_name='backendvalidationresult',
            name='speed',
            field=models.IntegerField(blank=True, help_text='Interface speed in Mbps', null=True),
        ),
    ]
