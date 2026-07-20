from django.db import migrations


def create_missing_rack_configurations(apps, schema_editor):
    """Backfill a RackConfiguration for every existing Rack that lacks one."""
    Rack = apps.get_model("data_center", "Rack")
    RackConfiguration = apps.get_model("switchports", "RackConfiguration")

    existing_rack_ids = set(
        RackConfiguration.objects.values_list("rack_id", flat=True)
    )
    missing_rack_ids = (
        Rack.objects.exclude(id__in=existing_rack_ids).values_list("id", flat=True)
    )
    RackConfiguration.objects.bulk_create(
        [RackConfiguration(rack_id=rack_id) for rack_id in missing_rack_ids],
        batch_size=1000,
    )


def noop(apps, schema_editor):
    # Irreversible on purpose: we cannot tell backfilled configurations apart
    # from ones created by users, so we do not delete anything on reverse.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("switchports", "0008_switchport_overrides_and_refresh_jobs"),
        ("data_center", "0044_remove_datacenterasset_connections_delete_connection"),
    ]

    operations = [
        migrations.RunPython(create_missing_rack_configurations, noop),
    ]
