# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from ralph.ui.views.common import Base
from ralph_assets.models_dc_assets import DataCenter


class DataCenterView(Base):
    submodule_name = 'dc_view'
    template_name = 'ui/data_center_view.html'

    def get_context_data(self, **kwargs):
        context = super(DataCenterView, self).get_context_data(**kwargs)
        context['data_centers'] = DataCenter.objects.all()
        return context
