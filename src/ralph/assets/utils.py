# -*- coding: utf-8 -*-
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import transaction


class DNSaaSPublisherMixin:
    """Generate data formatted for DNSaaS auto txt update"""

    def get_auto_txt_data(self):
        data = []
        for purpose_name, content in (
            (
                "class_name",
                self.configuration_path.class_name if self.configuration_path else "",
            ),  # noqa
            (
                "module_name",
                self.configuration_path.module.name if self.configuration_path else "",
            ),  # noqa
            (
                "configuration_path",
                self.configuration_path.path if self.configuration_path else "",
            ),  # noqa
            ("service_env", str(self.service_env) if self.service_env else ""),  # noqa
            ("model", str(self.model) if self.model else ""),
            ("location", " / ".join(self.get_location() or [])),
        ):
            purpose = settings.DNSAAS_AUTO_TXT_RECORD_PURPOSE_MAP.get(
                purpose_name, None
            )
            if not purpose or not content:
                continue
            update_def = {
                "ips": [ip.address for ip in self.ipaddresses if not ip.is_management],
                "purpose": purpose,
                "content": content,
            }
            service = self.service
            if service:
                update_def["service_uid"] = service.uid
            data.append(update_def)
        return data


@transaction.atomic
def move_parents_models(from_obj, to_obj, exclude_copy_fields=None):
    """
    Move parents Django model to diffrent model inheriting from
    the same parent.

    By default Django does not allow the remove of the model without parents.
    Clean _meta.parents, we remove object and add back default parents to class

    Args:
        from_obj: From Django model object
        to_obj: To Django modelo object
        exclude_copy_fields: Remove field from object dict

    Example:
        >> instance = DataCenterAsset.objects.get(pk=1)
        >> back_office_asset = BackOfficeAsset()
        >> move_parents_models(instance, back_office_asset)
    """
    from_dict = from_obj.__dict__
    if exclude_copy_fields:
        for field_name in exclude_copy_fields:
            field = to_obj._meta.get_field(field_name)
            from_dict.pop(field.name, None)
            from_dict.pop(field.attname, None)

    to_obj.__dict__.update(from_dict)
    to_obj.content_type = None
    to_obj.save()
    parents = from_obj._meta.parents
    from_obj._meta.parents = {}
    try:
        from_obj.delete()
    finally:
        from_obj._meta.parents = parents


def get_host_content_types():
    """
    Returns hosts content types.

    Proper content types:
    * Cluster
    * DataCenterAsset
    * VirtualServer
    * CloudHost
    """
    from ralph.data_center.models import Cluster, DataCenterAsset
    from ralph.virtual.models import CloudHost, VirtualServer

    return ContentType.objects.get_for_models(
        Cluster, DataCenterAsset, VirtualServer, CloudHost
    ).values()
