# -*- coding: utf-8 -*-
from ralph.admin.views.extra import RalphDetailView


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
        context['data_classification'] = [
            {'label': 'Availability', 'value': 'A3'},
            {'label': 'Confidentiality', 'value': 'C2'},
            {'label': 'Integrity', 'value': 'I4'},
        ]
        context['logs'] = [
            '/var/log',
        ]
        context['critical_pathes'] = [
            {
                'label': 'Critical Patch Update - April 2015',
                'value': 'Rev 3, 28 April 2015',
            },
            {
                'label': 'Critical Patch Update - January 2015',
                'value': 'Rev 2, 10 March 2015',
            },
            {
                'label': 'Critical Patch Update - October 2014',
                'value': 'Rev 5, 21 November 2014',
            },
            {
                'label': 'Critical Patch Update - July 2014',
                'value': 'Rev 2, 24 July 2014',
            },

        ]
        return context
