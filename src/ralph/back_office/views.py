# -*- coding: utf-8 -*-
from ralph.admin.views.extra import RalphDetailView


class BackOfficeAssetComponents(RalphDetailView):
    icon = "folder"
    name = "components"
    label = "Components"
    url_name = "back_office_asset_components"

    def get_context_data(self, **kwargs):
        context = super(BackOfficeAssetComponents, self).get_context_data(**kwargs)
        context["components"] = [
            {
                "label": "CPU 1",
                "model": "Intel(R) Xeon(R) CPU E5540 @ 2.53GHz",
                "serial_number": "",
                "speed": "2415 Mhz",
                "size": "4 core(s)",
                "count": "",
                "action": "",
            },
            {
                "label": "HDD",
                "model": "Baracuda",
                "serial_number": "SN/JKIO9009KL",
                "speed": "",
                "size": "120 GB",
                "count": "1",
                "action": "",
            },
            {
                "label": "RAM",
                "model": "Kingston",
                "serial_number": "SN/JKIO9009KDS",
                "speed": "",
                "size": "8 GB",
                "count": "1",
                "action": "",
            },
        ]
        return context


class BackOfficeAssetSoftware(RalphDetailView):
    icon = "wrench"
    name = "software"
    label = "Software"
    url_name = "back_office_asset_software"

    def get_context_data(self, **kwargs):
        context = super(BackOfficeAssetSoftware, self).get_context_data(**kwargs)
        context["software_list"] = [
            {
                "label": "Windows",
                "version": "8",
            },
            {
                "label": "OpenOffice",
                "version": "2.5.6",
            },
            {
                "label": "HipChat",
                "version": "50.6.0",
            },
            {
                "label": "ESET NOD32",
                "version": "1.5.0",
            },
        ]
        return context
