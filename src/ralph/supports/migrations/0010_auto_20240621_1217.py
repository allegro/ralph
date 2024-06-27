# Generated by Django 2.0.13 on 2024-06-21 12:17

from django.db import migrations
import django.db.models.deletion
import ralph.lib.mixins.fields


class Migration(migrations.Migration):

    dependencies = [
        ('supports', '0009_auto_20240506_1633'),
    ]

    operations = [
        migrations.AlterField(
            model_name='baseobjectssupport',
            name='baseobject',
            field=ralph.lib.mixins.fields.BaseObjectForeignKey(limit_choices_to=ralph.lib.mixins.fields.BaseObjectForeignKey.limit_choices, on_delete=django.db.models.deletion.CASCADE, related_name='supports', to='assets.BaseObject', verbose_name='Asset'),
        ),
    ]