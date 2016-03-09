# -*- coding: utf-8 -*-

from ralph.admin import RalphTabularInline
from ralph.admin.views.extra import RalphDetailViewAdmin
from ralph.dns.forms import DNSRecordInlineFormset
from ralph.dns.models import DNSRecord


class DNSInline(RalphTabularInline):
    formset = DNSRecordInlineFormset
    model = DNSRecord


class DNSView(RalphDetailViewAdmin):
    icon = 'chain'
    name = 'network'
    label = 'DNS'
    url_name = 'dns_edit'

    inlines = [DNSInline]
