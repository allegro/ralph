from ralph.data_center.publishers import publish_host_update
from ralph.lib.custom_fields.signals import api_post_create, api_post_update


def custom_field_change(sender, instance, **kwargs):
    from ralph.assets.utils import get_host_content_types
    content_type = getattr(instance.object, 'content_type', None)
    if not content_type or content_type not in get_host_content_types():
        return
    publish_host_update(instance.object)


api_post_create.connect(custom_field_change)
api_post_update.connect(custom_field_change)
