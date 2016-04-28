import logging
from functools import partial

from django.http import (
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseNotFound,
    HttpResponseNotModified
)
from django.utils.http import http_date, parse_http_date_safe
from django.views.generic.base import TemplateView
from rest_framework.views import APIView

from ralph.admin.helpers import get_client_ip
from ralph.assets.models.components import Ethernet
from ralph.data_center.models import DataCenter
from ralph.dhcp.models import DHCPEntry, DHCPServer
from ralph.networks.models.networks import (
    IPAddress,
    Network,
    NetworkEnvironment
)

logger = logging.getLogger(__name__)


class LastModifiedMixin(object):
    """Add last modified to HTTP response if last_modified attr is exist."""

    @classmethod
    def last(cls, qs, last_items=None, filter_dict=None):
        if filter_dict is None:
            filter_dict = {}
        item = qs.filter(**filter_dict).order_by('-modified').first()
        if last_items is None:
            return item.modified if item else None
        if item:
            last_items.append(item.modified)

    @property
    def last_timestamp(self):
        last_modified = getattr(self, 'last_modified', None)
        return last_modified and int(last_modified.timestamp())

    def is_modified(self, request):
        http_modified_since = request.META.get('HTTP_IF_MODIFIED_SINCE')
        if http_modified_since is None or self.last_timestamp is None:
            return True
        return self.last_timestamp > parse_http_date_safe(http_modified_since)

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        if not self.is_modified(request):
            return HttpResponseNotModified()
        response['Last-Modified'] = http_date(self.last_timestamp)
        return response


class DHCPConfigMixin(object):
    content_type = 'text/plain'

    @staticmethod
    def check_objects_existence_by_names(model_class, names):
        found = model_class.objects.filter(name__in=names)
        not_found = set(names) - set([obj.name for obj in found])
        return found, not_found

    def dispatch(self, request, *args, **kwargs):
        dc_names = request.GET.getlist('dc', None)
        env_names = request.GET.getlist('env', None)
        if dc_names and env_names:
            return HttpResponseBadRequest(
                'Only DC or ENV mode available.',
                content_type=self.content_type
            )

        if not (dc_names or env_names):
            return HttpResponseBadRequest(
                'Please specify DC or ENV.',
                content_type=self.content_type
            )

        if dc_names:
            found, not_found = self.check_objects_existence_by_names(
                DataCenter, dc_names
            )
            if not_found:
                return HttpResponseNotFound(
                    'DC: {} doesn\'t exists.'.format(', '.join(not_found)),
                    content_type='text/plain'
                )

            environments = NetworkEnvironment.objects.filter(
                data_center__in=found
            )
        elif env_names:
            found, not_found = self.check_objects_existence_by_names(
                NetworkEnvironment, env_names
            )
            if not_found:
                return HttpResponseNotFound(
                    'ENV: {} doesn\'t exists.'.format(', '.join(not_found)),
                    content_type='text/plain'
                )
            environments = found
        self.networks = Network.objects.select_related(
            'network_environment'
        ).filter(
            network_environment__in=environments,
            dhcp_broadcast=True,
        )
        self.last_modified = self.get_last_modified(self.networks)
        return super().dispatch(request, *args, **kwargs)


class DHCPSyncView(APIView):
    def get(self, request, *args, **kwargs):
        ip = get_client_ip(request)
        logger.info('Sync request DHCP server with IP: %s', ip)
        if not DHCPServer.update_last_synchronized(ip):
            return HttpResponseNotFound(
                'DHCP server doesn\'t exist.', content_type='text/plain'
            )
        return HttpResponse('OK', content_type='text/plain')


class DHCPEntriesView(
    DHCPConfigMixin, LastModifiedMixin, TemplateView, APIView
):
    http_method_names = ['get']
    template_name = 'dhcp/entries.conf'

    def get_last_modified(self, networks):
        """
        Return the latest date based on ``modified`` field from networks,
        IP (DHCP entry), ethernet.
        """
        last_items = []
        last = partial(self.last, last_items=last_items)

        last(networks)
        last(DHCPEntry.objects, filter_dict={
            'network__in': networks
        })
        last(Ethernet.objects, filter_dict={
            'ipaddress__network__in': networks
        })
        last(IPAddress.objects, filter_dict={
            'network__in': networks
        })
        if not last_items:
            return None
        return max(last_items)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'last_modified': self.last_modified,
            'entries': DHCPEntry.objects.filter(network__in=self.networks),
        })
        return context


class DHCPNetworksView(
    DHCPConfigMixin, LastModifiedMixin, TemplateView, APIView
):
    template_name = 'dhcp/networks.conf'

    def get_last_modified(self, networks):
        return self.last(networks)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        networks = self.networks.filter(
            network_environment__domain__isnull=False,
            dhcp_broadcast=True,
            ips__is_gateway=True,
        ).exclude(
            network_environment=False
        ).prefetch_related('dns_servers')
        context.update({
            'last_modified': self.last_modified,
            'entries': networks,
        })
        return context
