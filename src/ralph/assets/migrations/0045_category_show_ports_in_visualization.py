from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("assets", "0044_alter_service_options"),
    ]

    operations = [
        migrations.AddField(
            model_name="category",
            name="show_ports_in_visualization",
            field=models.BooleanField(
                default=False,
                verbose_name="show ports in rack visualization",
            ),
        ),
    ]
