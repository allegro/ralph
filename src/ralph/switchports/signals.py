from django.db.models.signals import post_save
from django.dispatch import receiver

from ralph.data_center.models.physical import Rack
from ralph.switchports.models import RackConfiguration


@receiver(post_save, sender=Rack, dispatch_uid="switchports_ensure_rack_configuration")
def ensure_rack_configuration(sender, instance, created, **kwargs):
    """Guarantee every Rack has a RackConfiguration.

    Creating a rack (via admin, API, import, factory, ...) always creates its
    RackConfiguration. Existing racks are backfilled by a data migration.
    """
    if created:
        RackConfiguration.objects.get_or_create(rack=instance)
