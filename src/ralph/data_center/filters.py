# -*- coding: utf-8 -*-
from django.utils.translation import ugettext_lazy as _

from ralph.admin.filters import TextFilter


class RackFilter(TextFilter):

    title = _('Rack')
    parameter_name = 'rack__name'
