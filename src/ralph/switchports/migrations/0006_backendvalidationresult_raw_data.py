from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('switchports', '0005_backendvalidationresult_admin_status_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='backendvalidationresult',
            name='raw_data',
            field=models.JSONField(blank=True, help_text='Full interface payload reported by the backend (netmaker)', null=True),
        ),
    ]
