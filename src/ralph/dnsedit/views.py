# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.http import HttpResponse
from ralph.ui.views.common import Base
from ralph.dnsedit.util import generate_dhcp_config

def dhcpd_config(request):
    return HttpResponse(generate_dhcp_config(), content_type="text/plain")

class Index(Base):
    template_name = 'dnsedit/index.html'
    section = 'dns'

    def __init__(self, *args, **kwargs):
        super(Index, self).__init__(*args, **kwargs)