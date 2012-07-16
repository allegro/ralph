# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import cStringIO as StringIO

from django.views.generic import ListView
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.http import HttpResponse
from django.core.paginator import InvalidPage
from django.http import Http404
from django.utils.translation import ugettext as _

from ralph.account.models import Perm
from ralph.util import csvutil


PAGE_SIZE = 25
DEVICE_SORT_COLUMNS = {
    'name': ('name',),
    'venture': ('venture', 'venture_role'),
    'model': ('model__type', 'model__name'),
    'margin': ('venture__margin_kind__margin', 'margin_kind__margin'),
    'deprecation': ('deprecation_kind__months',),
    'price': ('cached_price',),
    'cost': ('cached_cost',),
    'barcode': ('barcode',),
    'position': ('dc', 'rack', 'position', 'chassis_position'),
    'ips': ('ipaddress__address',),
    'management': ('management__address',),
    'created': ('created',),
    'lastseen': ('last_seen',),
    'remarks': ('remarks',),
    'purchase_date': ('purchase_date',),
    'warranty': ('warranty_expiration_date',),
    'support': ('support_expiration_date', 'support_kind'),
}


def _get_show_tabs(request, venture, device):
    if device and not venture:
        venture = device.venture
    if not venture or venture == '*':
        venture = None
    tabs = ['info']
    profile = request.user.get_profile()
    has_perm = profile.has_perm
    if has_perm(Perm.read_device_info_generic, venture):
        tabs.extend(['info', 'components', 'addresses', 'roles'])
    if has_perm(Perm.read_device_info_financial, venture):
        tabs.extend(['prices', 'costs'])
    if has_perm(Perm.list_devices_financial, venture):
        tabs.extend(['venture'])
    if has_perm(Perm.read_device_info_support, venture):
        tabs.extend(['purchase'])
    if has_perm(Perm.read_device_info_history, venture):
        tabs.extend(['history'])
    if has_perm(Perm.run_discovery, venture):
        tabs.extend(['discover'])
    #if has_perm(Perm.read_configuration_item_info_generic):
    tabs.extend(['cmdb'])

    return tabs


class BaseDeviceList(ListView):
    paginate_by = PAGE_SIZE
    details_columns = {
        'info': ['venture', 'model', 'position', 'remarks'],
        'components': ['model', 'barcode'],
        'prices': ['venture', 'margin', 'deprecation', 'price', 'cost'],
        'addresses': ['ips', 'management'],
        'costs': ['venture', 'cost'],
        'history': ['created', 'lastseen'],
        'purchase': ['pucrhase', 'warranty', 'support'],
        'discover': ['lastseen'],
        'cmdb': [],
        None: [],
    }

    def __init__(self, *args, **kwargs):
        super(BaseDeviceList, self).__init__(*args, **kwargs)
        self.tree = False
        self.venture = None
        self.sort = None

    def export_csv(self, query=None):
        if query is None:
            query = self.get_queryset()
        rows = [
            ['Id', 'Name', 'Venture', 'Role', 'Model', 'Data Center', 'Rack',
             'Position', 'Barcode', 'Margin', 'Deprecation', 'Price', 'Cost',
             'Addresses', 'Management', 'Created', 'Last Seen', 'Purchased',
             'Warranty Expiration', 'Support Expiration', 'Support Kind',
             'Serial Number', 'Remarks'],
        ]
        for dev in query.all():
            show_tabs = set(_get_show_tabs(self.request, None, dev))
            row = [
                str(dev.id),
                dev.name or '' if 'info' in show_tabs else '',
                dev.venture.symbol if dev.venture and 'info' in show_tabs else '',
                (dev.venture_role.full_name if dev.venture_role and
                    'info' in show_tabs else ''),
                dev.get_model_name() or '' if 'info' in show_tabs else '',
                dev.dc or '' if 'info' in show_tabs else '',
                dev.rack or '' if 'info' in show_tabs else '',
                dev.get_position() if 'info' in show_tabs else '',
                dev.barcode or '' if 'info' in show_tabs else '',
                str(dev.get_margin())+'%' if 'prices' in show_tabs else '',
                (dev.deprecation_kind.name if dev.deprecation_kind and
                    'prices' in show_tabs else ''),
                str(dev.cached_price) if 'prices' in show_tabs else '',
                str(dev.cached_cost) if 'costs' in show_tabs else '',
                ' '.join(ip.address for ip in dev.ipaddress_set.all()
                    ) if 'info' in show_tabs else '',
                dev.management or '' if 'info' in show_tabs else '',
                dev.created or '' if 'history' in show_tabs else '',
                dev.last_seen or '' if 'history' in show_tabs else '',
                dev.purchase_date or '' if 'purchase' in show_tabs else '',
                dev.warranty_expiration_date or ''if 'purchase' in show_tabs else '',
                dev.support_expiration_date or '' if 'purchase' in show_tabs else '',
                dev.support_kind or '' if 'purchase' in show_tabs else '',
                dev.sn or '' if 'purchase' in show_tabs else '',
                dev.remarks or '' if 'info' in show_tabs else '',
            ]
            rows.append([unicode(r) for r in row])
        f = StringIO.StringIO()
        csvutil.UnicodeWriter(f).writerows(rows)
        response = HttpResponse(f.getvalue(), content_type="application/csv")
        response['Content-Disposition'] = 'attachment; filename=ralph.csv'
        return response

    def user_allowed(self):
        return False

    def get(self, *args, **kwargs):
        if not self.user_allowed():
            messages.error(self.request, _("You don't have permission to view this."))
            return HttpResponseRedirect('..')
        export = self.request.GET.get('export')
        if export == 'csv':
            return self.export_csv()
        return super(BaseDeviceList, self).get(*args, **kwargs)

    def sort_queryset(self, queryset, columns=DEVICE_SORT_COLUMNS, sort=None):
        if sort is None:
            sort = self.request.GET.get('sort', '')
        sort_columns = columns.get(sort.strip('-'), ())
        if sort.startswith('-'):
            sort_columns = ['-' + col for col in sort_columns]
        if queryset and sort:
            queryset = queryset.order_by(*sort_columns)
        self.sort = sort
        return queryset

    def get_queryset(self, queryset=None):
        if queryset is None:
            queryset = super(BaseDeviceList, self).get_queryset()
        return self.sort_queryset(queryset, columns=DEVICE_SORT_COLUMNS)

    def get_paginator_links(self, paginator, page_no):
        pages = paginator.page_range[max(0, page_no - 2):
                                     min(paginator.num_pages, page_no + 1)]
        if 1 not in pages:
            pages.insert(0, 1)
            pages.insert(1, '...')
        if paginator.num_pages not in pages:
            pages.append('...')
            pages.append(paginator.num_pages)
        return pages

    def get_context_data(self, **kwargs):
        ret = super(BaseDeviceList, self).get_context_data(**kwargs)
        details = self.kwargs.get('details', 'info')
        if ret['is_paginated']:
            paginator_links = self.get_paginator_links(ret['paginator'],
                                                        ret['page_obj'].number)
        else:
            paginator_links = []
        ret.update({
            'paginator_links': paginator_links,
            'columns': self.details_columns.get(details, self.details_columns[None]),
            'show_tabs': _get_show_tabs(self.request, self.venture, None),
            'sort': self.sort,
        })
        return ret

    def get_template_names(self):
        return ['ui/device_list.html']

    def paginate_queryset(self, queryset, page_size):
        """
        Paginate the queryset, if needed. When page number is 0, don't paginate.
        """
        paginator = self.get_paginator(queryset, page_size,
                        allow_empty_first_page=self.get_allow_empty())
        page = self.kwargs.get('page')
        if page is None:
            page = self.request.GET.get('page')
        if page is None:
            page = 1
        try:
            page_number = int(page)
        except ValueError:
            if page == 'last':
                page_number = paginator.num_pages
            else:
                raise Http404(
                _(u"Page is not 'last', nor can it be converted to an int."))
        if page_number == 0:
            return (None, None, queryset, False)
        try:
            page = paginator.page(page_number)
            return (paginator, page, page.object_list, page.has_other_pages())
        except InvalidPage:
            raise Http404(_(u'Invalid page (%(page_number)s)') % {
                                'page_number': page_number
            })
