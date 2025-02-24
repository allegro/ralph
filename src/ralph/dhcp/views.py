import logging

from django.db.models import Count, Prefetch
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
from ralph.deployment.models import Deployment
from ralph.dhcp.models import DHCPEntry, DHCPServer, DNSServer
from ralph.networks.models.networks import (
    IPAddress,
    Network,
    NetworkEnvironment
)

logger = logging.getLogger(__name__)


def last_modified_date(qs, filter_dict=None):
    last_date = None
    if filter_dict is None:
        filter_dict = {}
    obj = qs.filter(**filter_dict).order_by("-modified").first()
    if obj:
        last_date = obj.modified
    return last_date


class LastModifiedMixin(object):
    """Add last modified to HTTP response if last_modified attr is exist."""

    @property
    def last_timestamp(self):
        last_modified = getattr(self, "last_modified", None)
        return last_modified and int(last_modified.timestamp())

    def is_modified(self, request):
        http_modified_since = request.META.get("HTTP_IF_MODIFIED_SINCE")
        if http_modified_since is None or self.last_timestamp is None:
            return True
        return self.last_timestamp > parse_http_date_safe(http_modified_since)

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        if not self.is_modified(request):
            return HttpResponseNotModified()
        response["Last-Modified"] = http_date(self.last_timestamp)
        return response


class DHCPConfigMixin(object):
    content_type = "text/plain"

    @staticmethod
    def check_objects_existence_by_names(model_class, names):
        found = model_class.objects.filter(name__in=names)
        not_found = set(names) - set([obj.name for obj in found])
        return found, not_found

    def dispatch(self, request, *args, **kwargs):
        dc_names = request.GET.getlist("dc", None)
        env_names = request.GET.getlist("env", None)
        if dc_names and env_names:
            return HttpResponseBadRequest(
                "Only DC or ENV mode available.", content_type=self.content_type
            )

        if not (dc_names or env_names):
            return HttpResponseBadRequest(
                "Please specify DC or ENV.", content_type=self.content_type
            )

        if dc_names:
            found, not_found = self.check_objects_existence_by_names(
                DataCenter, dc_names
            )
            if not_found:
                return HttpResponseNotFound(
                    "DC: {} doesn't exists.".format(", ".join(not_found)),
                    content_type="text/plain",
                )

            environments = NetworkEnvironment.objects.filter(data_center__in=found)
        elif env_names:
            found, not_found = self.check_objects_existence_by_names(
                NetworkEnvironment, env_names
            )
            if not_found:
                return HttpResponseNotFound(
                    "ENV: {} doesn't exists.".format(", ".join(not_found)),
                    content_type="text/plain",
                )
            environments = found
        self.networks = Network.objects.select_related("network_environment").filter(
            network_environment__in=environments,
            dhcp_broadcast=True,
        )
        self.last_modified = self.get_last_modified(self.networks)
        return super().dispatch(request, *args, **kwargs)


class DHCPSyncView(APIView):
    def get(self, request, *args, **kwargs):
        ip = get_client_ip(request)
        logger.info("Sync request DHCP server with IP: %s", ip)
        if not DHCPServer.update_last_synchronized(ip):
            return HttpResponseNotFound(
                "DHCP server doesn't exist.", content_type="text/plain"
            )
        return HttpResponse("OK", content_type="text/plain")


class DHCPEntriesView(DHCPConfigMixin, LastModifiedMixin, TemplateView, APIView):
    http_method_names = ["get"]
    template_name = "dhcp/entries.conf"

    def get_last_modified(self, networks):
        """
        Return the latest date based on ``modified`` field from networks,
        IP (DHCP entry), ethernet.
        """
        last_items = []

        try:
            last_items.append(Deployment.objects.latest("modified").modified)
        except Deployment.DoesNotExist:
            pass
        last_items.append(last_modified_date(networks))
        last_items.append(
            last_modified_date(DHCPEntry.objects, filter_dict={"network__in": networks})
        )
        last_items.append(
            last_modified_date(
                Ethernet.objects, filter_dict={"ipaddress__network__in": networks}
            )
        )
        last_items.append(
            last_modified_date(IPAddress.objects, filter_dict={"network__in": networks})
        )
        last_items = [item for item in last_items if item is not None]
        if not last_items:
            return None
        return max(last_items)

    def _filter_dhcp_entries(self, entries):
        """
        Exclude entries with duplicated hostnames.
        """
        duplicated_hostnames = [
            e["hostname"]
            for e in entries.values("hostname").annotate(c=Count("id")).filter(c__gt=1)
        ]
        for hostname in duplicated_hostnames:
            logger.error("Duplicated hostname for DHCP entry: %s", hostname)
        return entries.exclude(hostname__in=duplicated_hostnames)

    def _get_dhcp_entries(self, networks):
        """
        Returns filtered DHCP entries for given networks.
        """
        return self._filter_dhcp_entries(
            DHCPEntry.objects.filter(network__in=networks).order_by("hostname")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "last_modified": self.last_modified,
                "entries": self._get_dhcp_entries(self.networks),
            }
        )
        return context


class DHCPNetworksView(DHCPConfigMixin, LastModifiedMixin, TemplateView, APIView):
    template_name = "dhcp/networks.conf"

    def get_last_modified(self, networks):
        last_items = []
        last_items.append(last_modified_date(networks))
        last_items.append(
            last_modified_date(
                NetworkEnvironment.objects, filter_dict={"network__in": networks}
            )
        )
        last_items.append(
            last_modified_date(
                IPAddress.objects,
                filter_dict={"network__in": networks, "is_gateway": True},
            )
        )
        last_items = [item for item in last_items if item is not None]
        if not last_items:
            return None
        return max(last_items)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        networks = (
            self.networks.filter(
                network_environment__domain__isnull=False,
                dhcp_broadcast=True,
                gateway__isnull=False,
            )
            .exclude(network_environment=False)
            .select_related("dns_servers_group", "gateway")
            .prefetch_related(
                Prefetch(
                    "dns_servers_group__server_group_order__dns_server",
                    queryset=DNSServer.objects.all().order_by(
                        "server_group_order__order"
                    ),
                )
            )
        )
        context.update(
            {
                "last_modified": self.last_modified,
                "entries": networks,
            }
        )
        return context
