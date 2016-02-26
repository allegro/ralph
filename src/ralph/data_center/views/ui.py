# -*- coding: utf-8 -*-
from ralph.admin.views.extra import RalphDetailView
from ralph.security.models import SecurityScan


class DataCenterAssetSecurityInfo(
    RalphDetailView
):

    icon = 'lock'
    label = 'Security Info'
    name = 'security_info'
    url_name = 'datacenter_asset_security_info'

    def get_context_data(self, **kwargs):
        context = super(DataCenterAssetSecurityInfo, self).get_context_data(
            **kwargs
        )
        context['security_scan'] = SecurityScan.objects.filter(
            base_object=self.object).last()
        return context
