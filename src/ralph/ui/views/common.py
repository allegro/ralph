# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import datetime

from django.conf import settings
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, EmptyPage
from django.db import models as db
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.utils import simplejson as json
from django.views.generic import UpdateView, DetailView, TemplateView

from lck.django.common import nested_commit_on_success
from lck.django.tags.models import Language, TagStem
from bob.menu import MenuItem
from powerdns.models import Record

from ralph.account.models import Perm
from ralph.business.models import RolePropertyValue
from ralph.cmdb import models as cdb
from ralph.dnsedit.models import DHCPEntry
from ralph.discovery.models import Device, DeviceType
from ralph.util import presentation, pricing
from ralph.ui.forms import (DeviceInfoForm, DeviceInfoVerifiedForm,
                            DevicePricesForm, DevicePurchaseForm,
                            PropertyForm, DeviceBulkForm)


SAVE_PRIORITY = 200
HISTORY_PAGE_SIZE = 25
MAX_PAGE_SIZE = 65535


def _get_balancers(dev):
    for ip in dev.ipaddress_set.select_related().all():
        for member in ip.loadbalancermember_set.order_by('device'):
            yield {
                    'balancer': member.device.name,
                    'pool': member.pool.name,
                    'enabled': member.enabled,
                    'server': None,
                    'port': member.port,
            }
    for vserv in dev.loadbalancervirtualserver_set.all():
        yield {
            'balancer': dev.name,
            'pool': vserv.default_pool.name,
            'enabled': None,
            'server': vserv.name,
            'port': vserv.port,
        }

def _get_details(dev, purchase_only=False, with_price=False):
    for detail in pricing.details_all(dev, purchase_only):
        if 'icon' not in detail:
            if detail['group'] == 'dev':
                detail['icon'] = presentation.get_device_model_icon(detail.get('model'))
            else:
                detail['icon'] = presentation.get_component_model_icon(detail.get('model'))
        if 'price' not in detail:
            if detail.get('model'):
                detail['price'] = detail['model'].get_price()
            else:
                detail['price'] = None
        if with_price and not detail['price']:
            continue
        if detail['group'] != 'dev' and 'size' not in detail and detail.get('model'):
            detail['size'] = detail['model'].size
        if detail.get('model'):
            if detail['model'].group:
                detail['modelgroup'] = detail['model'].group
                detail['model'] = detail['model'].group.name
            else:
                detail['model'] = detail['model'].name
        else:
            detail['model'] = detail.get('model_name', '')
        yield detail


class BaseMixin(object):
    section = 'home'

    def __init__(self, *args, **kwargs):
        super(BaseMixin, self).__init__(*args, **kwargs)
        self.venture = None
        self.object = None

    def get_context_data(self, **kwargs):
        ret = super(BaseMixin, self).get_context_data(**kwargs)
        details = self.kwargs.get('details', 'info')
        profile = self.request.user.get_profile()
        has_perm = profile.has_perm
        footer_items = []
        mainmenu_items = [
            MenuItem('Ventures', fugue_icon='fugue-store',
                     view_name='ventures')
        ]
        if has_perm(Perm.read_dc_structure):
            mainmenu_items.append(
                MenuItem('Racks', fugue_icon='fugue-building',
                         view_name='racks'))
        if has_perm(Perm.read_network_structure):
            mainmenu_items.append(
                MenuItem('Networks', fugue_icon='fugue-weather-clouds',
                         view_name='networks'))
        if has_perm(Perm.read_device_info_reports):
            mainmenu_items.append(
                MenuItem('Reports', fugue_icon='fugue-report',
                         view_name='reports'))
        if has_perm(Perm.edit_device_info_financial):
            mainmenu_items.append(
                MenuItem('Catalog', fugue_icon='fugue-paper-bag',
                         view_name='catalog'))
        if ('ralph.cmdb' in settings.INSTALLED_APPS and
                has_perm(Perm.read_configuration_item_info_generic)):
            mainmenu_items.append(
                MenuItem('CMDB', fugue_icon='fugue-thermometer',
                         href='/cmdb/changes/timeline')
            )
        if settings.BUGTRACKER_URL:
            footer_items.append(
                MenuItem('Bugs', fugue_icon='fugue-bug',
                         href=settings.BUGTRACKER_URL))
        if self.request.user.is_staff:
            footer_items.append(
                MenuItem('Admin', fugue_icon='fugue-toolbox', href='/admin'))
        footer_items.append(
            MenuItem('%s (logout)' % self.request.user, fugue_icon='fugue-user',
                     view_name='logout', view_args=[details or 'info', ''],
                     pull_right=True))
        mainmenu_items.append(
            MenuItem('Advanced search', name='search',
                     fugue_icon='fugue-magnifier', view_args=[details or 'info', ''],
                     view_name='search', pull_right=True))
        tab_items = []
        venture = (
                self.venture if self.venture and self.venture != '*' else None
            ) or (
                self.object.venture if self.object else None
            )
        def tab_href(name):
            return '../%s/%s?%s' % (
                    name,
                    self.object.id if self.object else '',
                    self.request.GET.urlencode()
                )
        if has_perm(Perm.read_device_info_generic, venture):
            tab_items.extend([
                MenuItem('Info', fugue_icon='fugue-wooden-box',
                         href=tab_href('info')),
                MenuItem('Components', fugue_icon='fugue-box',
                        href=tab_href('components')),
                MenuItem('Addresses', fugue_icon='fugue-network-ip',
                        href=tab_href('addresses')),
            ])
        if has_perm(Perm.edit_device_info_financial, venture):
            tab_items.extend([
                MenuItem('Prices', fugue_icon='fugue-money-coin',
                        href=tab_href('prices')),
            ])
        if has_perm(Perm.read_device_info_financial, venture):
            tab_items.extend([
                MenuItem('Costs', fugue_icon='fugue-wallet',
                        href=tab_href('costs')),
            ])
        if has_perm(Perm.read_device_info_history, venture):
            tab_items.extend([
                MenuItem('History', fugue_icon='fugue-hourglass',
                         href=tab_href('history')),
            ])
        if has_perm(Perm.read_device_info_support, venture):
            tab_items.extend([
                MenuItem('Purchase', fugue_icon='fugue-baggage-cart-box',
                         href=tab_href('purchase')),
            ])
        if has_perm(Perm.run_discovery, venture):
            tab_items.extend([
                MenuItem('Discover', fugue_icon='fugue-flashlight',
                         href=tab_href('discover')),
            ])
        if ('ralph.cmdb' in settings.INSTALLED_APPS and
            has_perm(Perm.read_configuration_item_info_generic)):
            tab_items.extend([
                MenuItem('CMDB', fugue_icon='fugue-thermometer',
                         href=tab_href('cmdb')),
            ])
        if has_perm(Perm.read_device_info_reports, venture):
            tab_items.extend([
                MenuItem('Reports', fugue_icon='fugue-reports-stack',
                         href=tab_href('reports')),
            ])
        if details == 'bulkedit':
            tab_items.extend([
                MenuItem('Bulk edit', fugue_icon='fugue-pencil-field',
                         name='bulkedit'),
            ])
        ret.update({
            'section': self.section,
            'details': details,
            'mainmenu_items': mainmenu_items,
            'footer_items': footer_items,
            'url_query': self.request.GET,
            'search_url': reverse('search', args=[details, '']),
            'user': self.request.user,
            'tab_items': tab_items,
            'show_bulk': has_perm(Perm.bulk_edit),
        })
        return ret


class Base(BaseMixin, TemplateView):
    columns = []

    def get_context_data(self, **kwargs):
        ret = super(Base, self).get_context_data(**kwargs)
        ret.update({
            'columns': self.columns,
        })
        return ret


class Home(Base):
    template_name = 'ui/home.html'

    def get_context_data(self, **kwargs):
        ret = super(Home, self).get_context_data(**kwargs)
        profile = self.request.user.get_profile()
        devices = TagStem.objects.get_content_objects(author=profile)
        for d in devices:
            tags = d.get_tags(official=False, author=profile)
            tags = ['"%s"' % t.name if ',' in t.name else t.name for t in tags]
            d.tag_str = ', '.join(tags)
        ret.update({
            'devices': devices,
        })
        return ret


class DeviceUpdateView(UpdateView):
    model = Device
    slug_field = 'id'
    slug_url_kwarg = 'device'

    def get_success_url(self):
        return self.request.path

    def get_template_names(self):
        return [self.template_name]

    def get_context_data(self, **kwargs):
        ret = super(DeviceUpdateView, self).get_context_data(**kwargs)
        has_perm = self.request.user.get_profile().has_perm
        ret.update({
            'device': self.object,
            'editable': has_perm(self.edit_perm, self.object.venture),
        })
        return ret

    def form_valid(self, form):
        model = form.save(commit=False)
        model.save_comment = form.cleaned_data.get('save_comment')
        model.save(priority=SAVE_PRIORITY, user=self.request.user)
        pricing.device_update_cached(model)
        messages.success(self.request, "Changes saved.")
        return HttpResponseRedirect(self.request.path)

    def get(self, *args, **kwargs):
        self.object = self.get_object()
        has_perm = self.request.user.get_profile().has_perm
        if not has_perm(self.read_perm, self.object.venture):
            return HttpResponseForbidden("You don't have permission to see this.")
        return super(DeviceUpdateView, self).get(*args, **kwargs)

    def post(self, *args, **kwargs):
        self.object = self.get_object()
        has_perm = self.request.user.get_profile().has_perm
        if not has_perm(self.edit_perm, self.object.venture):
            return HttpResponseForbidden("You don't have permission to edit this.")
        return super(DeviceUpdateView, self).post(*args, **kwargs)


class DeviceDetailView(DetailView):
    model = Device
    slug_field = 'id'
    slug_url_kwarg = 'device'

    def get_template_names(self):
        return [self.template_name]

    def get_context_data(self, **kwargs):
        ret = super(DeviceDetailView, self).get_context_data(**kwargs)
        ret.update({
            'device': self.object,
        })
        return ret

    def get(self, *args, **kwargs):
        self.object = self.get_object()
        has_perm = self.request.user.get_profile().has_perm
        if not has_perm(self.read_perm, self.object.venture):
            return HttpResponseForbidden("You don't have permission to see this.")
        return super(DeviceDetailView, self).get(*args, **kwargs)


class Info(DeviceUpdateView):
    template_name = 'ui/device_info.html'
    read_perm = Perm.read_device_info_generic
    edit_perm = Perm.edit_device_info_generic

    def get_form_class(self):
        if self.object.verified:
            return DeviceInfoVerifiedForm
        return DeviceInfoForm

    def get_initial(self):
        return {
            'model_name': self.object.get_model_name(),
            'rack_name': self.object.rack,
            'dc_name': self.object.dc,
        }

    def get_context_data(self, **kwargs):
        ret = super(Info, self).get_context_data(**kwargs)
        if self.object:
            tags = self.object.get_tags(official=False,
                                      author=self.request.user)
        else:
            tags = []
        tags = ['"%s"' % t.name if ',' in t.name else t.name for t in tags]
        ret.update({
            'property_form': self.property_form,
            'tags': ', '.join(tags),
            'dt': DeviceType,
        })
        return ret

    def get(self, *args, **kwargs):
        self.object = self.get_object()
        self.property_form = self.get_property_form()
        return super(Info, self).get(*args, **kwargs)

    def save_properties(self, device, properties):
        for symbol, value in properties.iteritems():
            p = device.venture_role.roleproperty_set.get(symbol=symbol)
            pv, created = RolePropertyValue.concurrent_get_or_create(property=p, device=device)
            pv.value = value
            pv.save()

    def get_property_form(self):
        props = {}
        if not self.object.venture_role:
            return None
        for p in self.object.venture_role.roleproperty_set.all():
            try:
                value = p.rolepropertyvalue_set.filter(device=self.object)[0].value
            except IndexError:
                value = ''
            props[p.symbol] = value
        properties = list(self.object.venture_role.roleproperty_set.all())
        if not properties:
            return None
        return PropertyForm(properties, initial=props)

    def post(self, *args, **kwargs):
        self.object = self.get_object()
        has_perm = self.request.user.get_profile().has_perm
        if not has_perm(Perm.edit_device_info_generic, self.object.venture):
            return HttpResponseForbidden("You don't have permission to edit this.")
        self.property_form = self.get_property_form()
        if 'propertiessave' in self.request.POST:
            properties = list(self.object.venture_role.roleproperty_set.all())
            self.property_form = PropertyForm(properties, self.request.POST)
            if self.property_form.is_valid():
                messages.success(self.request, "Properties updated.")
                self.save_properties(self.object, self.property_form.cleaned_data)
                return HttpResponseRedirect(self.request.path)
        elif 'save-tags' in self.request.POST:
            tags = self.request.POST.get('tags', '')
            self.object.untag_all()
            self.object.tag(tags, Language.en, self.request.user)
            messages.success(self.request, "Tags updated.")
            return HttpResponseRedirect(self.request.path)
        else:
            return super(Info, self).post(*args, **kwargs)
        return super(Info, self).get(*args, **kwargs)


class Components(DeviceDetailView):
    template_name = 'ui/device_components.html'
    read_perm = Perm.read_device_info_generic

    def get_context_data(self, **kwargs):
        ret = super(Components, self).get_context_data(**kwargs)
        ret.update({
            'components': _get_details(self.object, purchase_only=False),
        })
        return ret


class Prices(DeviceUpdateView):
    form_class = DevicePricesForm
    template_name = 'ui/device_prices.html'
    read_perm = Perm.edit_device_info_financial # sic
    edit_perm = Perm.edit_device_info_financial

    def get_initial(self):
        return {
            'auto_price': pricing.get_device_raw_price(self.object)
        }

    def get_context_data(self, **kwargs):
        ret = super(Prices, self).get_context_data(**kwargs)
        ret.update({
            'components': _get_details(self.object,
                                       purchase_only=False,
                                       with_price=True),
        })
        return ret


class Addresses(DeviceDetailView):
    template_name = 'ui/device_addresses.html'
    read_perm = Perm.read_device_info_generic

    def get_dns(self):
        ips = set(ip.address for ip in self.object.ipaddress_set.all())
        names = set(ip.hostname for ip in self.object.ipaddress_set.all()
                 if ip.hostname)
        dotnames = set(name+'.' for name in names)
        for entry in Record.objects.filter(
                db.Q(content__in=ips) |
                db.Q(name__in=names) |
                db.Q(content__in=names | dotnames)
            ):
            names.add(entry.name)
            if entry.type == 'A':
                ips.add(entry.content)
            elif entry.type == 'CNAME':
                names.add(entry.content)
        for entry in Record.objects.filter(
                db.Q(content__in=ips) |
                db.Q(name__in=names) |
                db.Q(content__in=names)
            ):
            yield entry


    def get_dhcp(self):
        macs = set(eth.mac for eth in self.object.ethernet_set.all())
        return DHCPEntry.objects.filter(mac__in=macs)

    def get_context_data(self, **kwargs):
        ret = super(Addresses, self).get_context_data(**kwargs)
        ret.update({
            'balancers': list(_get_balancers(self.object)),
            'dns': self.get_dns(),
            'dhcp': self.get_dhcp(),
        })
        return ret


class Costs(DeviceDetailView):
    template_name = 'ui/device_costs.html'
    read_perm = Perm.list_devices_financial

    def get_context_data(self, **kwargs):
        query_variable_name = 'cost_page'
        ret = super(Costs, self).get_context_data(**kwargs)
        history = self.object.historycost_set.order_by('-end', '-start').all()
        has_perm = self.request.user.get_profile().has_perm
        for h in history:
            if not has_perm(Perm.list_devices_financial, h.venture):
                h.daily_cost = None
            if h.end.year != 9999 and h.start:
                h.span = (h.end - h.start).days
            elif h.start:
                h.span = (datetime.date.today() - h.start).days
        try:
            page = max(1, int(self.request.GET.get(query_variable_name, 1)))
        except ValueError:
            page = 1
        history_page = Paginator(history, HISTORY_PAGE_SIZE).page(page)
        ret.update({
            'history': history,
            'history_page': history_page,
            'query_variable_name': query_variable_name,
        })
        last_month = datetime.date.today() - datetime.timedelta(days=31)
        splunk = self.object.splunkusage_set.filter(
                day__gte=last_month
            ).order_by('-day')
        if splunk.count():
            size = splunk.aggregate(db.Sum('size'))['size__sum'] or 0
            cost = splunk[0].get_price(size=size) / splunk[0].model.group.size_modifier
            ret.update({
                'splunk_size': size,
                'splunk_monthly_cost': cost,
                'splunk_daily_cost': cost / splunk.count(),
            })
        return ret


class History(DeviceDetailView):
    template_name = 'ui/device_history.html'
    read_perm = Perm.read_device_info_history

    def get_context_data(self, **kwargs):
        query_variable_name = 'history_page'
        ret = super(History, self).get_context_data(**kwargs)
        history = self.object.historychange_set.order_by('-date')
        show_all = bool(self.request.GET.get('all', ''))
        if not show_all:
            history = history.exclude(user=None)
        try:
            page = int(self.request.GET.get(query_variable_name, 1))
        except ValueError:
            page = 1
        if page == 0:
            page = 1
            page_size = MAX_PAGE_SIZE
        else:
            page_size = HISTORY_PAGE_SIZE
        history_page = Paginator(history, HISTORY_PAGE_SIZE).page(page)
        ret.update({
            'history': history,
            'history_page': history_page,
            'show_all': show_all,
            'query_variable_name': query_variable_name,
        })
        return ret


class Purchase(DeviceUpdateView):
    form_class = DevicePurchaseForm
    template_name = 'ui/device_purchase.html'
    read_perm = Perm.read_device_info_support
    edit_perm = Perm.edit_device_info_support

    def get_initial(self):
        return {
            'model_name': self.object.get_model_name()
        }

    def get_context_data(self, **kwargs):
        ret = super(Purchase, self).get_context_data(**kwargs)
        ret.update({
            'components': _get_details(self.object, purchase_only=False, with_price=True),
        })
        return ret


class Discover(DeviceDetailView):
    template_name = 'ui/device_discover.html'
    read_perm = Perm.run_discovery

    def get_context_data(self, **kwargs):
        ret = super(Discover, self).get_context_data(**kwargs)
        addresses = [ip.address for ip in self.object.ipaddress_set.all()]
        ret.update({
            'address': addresses[0] if addresses else '',
            'addresses': json.dumps(addresses)
        })
        return ret


@nested_commit_on_success
def bulk_update(devices, fields, data, user):
    for d in devices:
        if 'venture' in fields:
            d.venture_role = None
        for name in fields:
            setattr(d, name, data[name])
        d.save_comment = data.get('save_comment')
        d.save(priority=SAVE_PRIORITY, user=user)
        pricing.device_update_cached(d)


class BulkEdit(BaseMixin, TemplateView):
    template_name = 'ui/bulk-edit.html'
    Form = DeviceBulkForm

    def __init__(self, *args, **kwargs):
        super(BulkEdit, self).__init__(*args, **kwargs)
        self.form = None
        self.devices = []
        self.edit_fields = []
        self.different_fields = []

    def post(self, *args, **kwargs):
        profile = self.request.user.get_profile()
        if not profile.has_perm(Perm.bulk_edit):
            messages.error(self.request, "You don't have permissions for bulk edit.")
            return super(BulkEdit, self).get(*args, **kwargs)
        selected = self.request.POST.getlist('select')
        self.devices = Device.objects.filter(id__in=selected)
        self.edit_fields = self.request.POST.getlist('edit')
        initial = {}
        self.different_fields = []
        for name in self.Form().fields:
            if name == 'save_comment':
                continue
            query = Device.objects.filter(id__in=selected).values(name).distinct()
            if query.count() > 1:
                self.different_fields.append(name)
            elif query.count() > 0:
                initial[name] = query[0][name]
        if 'save' in self.request.POST:
            self.form = self.Form(self.request.POST, initial=initial)
            if self.form.is_valid():
                bulk_update(self.devices, self.edit_fields,
                        self.form.cleaned_data, self.request.user)
                return HttpResponseRedirect(self.request.path+'../info/')
            else:
                messages.error(self.request, 'Correct the errors.')
        elif 'bulk' in self.request.POST:
            self.form = self.Form(initial=initial)
        return super(BulkEdit, self).get(*args, **kwargs)

    def get(self, *args, **kwargs):
        return super(BulkEdit, self).get(*args, **kwargs)

    def get_context_data(self, **kwargs):
        ret = super(BulkEdit, self).get_context_data(**kwargs)
        ret.update({
            'form': self.form,
            'details': 'bulkedit',
            'section': self.kwargs.get('section'),
            'subsection': 'bulk edit',
            'devices': self.devices,
            'edit_fields': self.edit_fields,
            'different_fields': self.different_fields,
        })
        return ret



class CMDB(BaseMixin):
    template_name = 'cmdb/ralph_view_ci.html'
    read_perm = Perm.read_configuration_item_info_generic

    def get_context_data(self, **kwargs):
        ret = super(CMDB, self).get_context_data(**kwargs)
        device_id = self.kwargs.get('device')
        try:
            ci=cdb.CI.objects.get(
                    type=cdb.CI_TYPES.DEVICE.id,
                    object_id=device_id
            )
        except:
            ci = None
        ret.update({
            'ci': ci,
            'url_query': self.request.GET,
            'components': _get_details(self.object, purchase_only=False),
        })
        return ret