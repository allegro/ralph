import logging
from functools import partial, wraps

from django.contrib.admin.utils import get_model_from_relation

from ralph.admin.helpers import get_field_by_relation_path
from ralph.assets.models import BaseObject
from ralph.data_center.publishers import (
    publish_host_update,
    publish_host_update_from_related_model
)
from ralph.lib.custom_fields.signals import api_post_create, api_post_update
from ralph.signals import post_commit

logger = logging.getLogger(__name__)


def custom_field_change(sender, instance, **kwargs):
    from ralph.assets.utils import get_host_content_types

    content_type = getattr(instance.object, "content_type", None)
    if not content_type or content_type not in get_host_content_types():
        return
    publish_host_update(instance.object)


api_post_create.connect(custom_field_change)
api_post_update.connect(custom_field_change)

# trigger publish_host_update when related model change
for model_path in [
    "configuration_path",
    "configuration_path__module",
    "ethernet_set",
    "ethernet_set__ipaddress",
]:
    field = get_field_by_relation_path(BaseObject, model_path)
    model = get_model_from_relation(field)
    logger.debug(
        "Setting up handler for {} change of BaseObject".format(
            model.__name__,
        )
    )
    post_commit(
        # use wraps for keep magic attributes of func like __name__
        wraps(publish_host_update_from_related_model)(
            partial(publish_host_update_from_related_model, field_path=model_path)
        ),
        model,
    )
