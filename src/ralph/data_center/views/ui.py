# -*- coding: utf-8 -*-
from ralph.admin.views.extra import RalphDetailView
from ralph.security.models import SecurityScan


class DataCenterAssetComponents(RalphDetailView):

    icon = 'folder'
    label = 'Components'
    name = 'components'
    url_name = 'datacenter_asset_components'

    def get_context_data(self, **kwargs):
        context = super(DataCenterAssetComponents, self).get_context_data(
            **kwargs
        )
        context['components'] = [
            {
                'label': 'CPU 1',
                'model': 'Intel(R) Xeon(R) CPU E5540 @ 2.53GHz',
                'serial_number': '',
                'speed': '2415 Mhz',
                'size': '4 core(s)',
                'count': '',
                'action': '',
            },
            {
                'label': 'CPU 2',
                'model': 'Intel(R) Xeon(R) CPU E5540 @ 2.53GHz',
                'serial_number': '',
                'speed': '2415 Mhz',
                'size': '4 core(s)',
                'count': '',
                'action': '',
            },
            {
                'label': 'PROC 1 DIMM 2',
                'model': 'RAM 4096MiB, 1333MHz',
                'serial_number': '',
                'speed': '1333 Mhz',
                'size': '4096 MiB',
                'count': '',
                'action': '',
            },
            {
                'label': 'HP DG0300BALVP SAS',
                'model': 'HP DG0300BALVP 307200MiB',
                'serial_number': 'SN/UYKJSH72829JJ',
                'speed': '',
                'size': '307200 MiB',
                'count': '',
                'action': '',
            },
        ]
        return context


class DataCenterAssetSoftware(
    RalphDetailView
):

    icon = 'wrench'
    label = 'Software'
    name = 'software'
    url_name = 'datacenter_asset_software'

    def get_context_data(self, **kwargs):
        context = super(DataCenterAssetSoftware, self).get_context_data(
            **kwargs
        )
        context['software_list'] = [
            {'label': 'acl', 'version': '2.2.6'},
            {'label': 'apr', 'version': '2.5.6'},
            {'label': 'aspel-en', 'version': '50.6.0'},
            {'label': 'audit', 'version': '1.5.0'},
        ]
        return context


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
