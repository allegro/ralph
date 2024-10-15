from django.conf.urls import url

from ralph.dhcp.views import DHCPEntriesView, DHCPNetworksView, DHCPSyncView

urlpatterns = [
    url(r"^sync/?$", DHCPSyncView.as_view(), name="dhcp_config_sync"),
    url(r"^entries/?$", DHCPEntriesView.as_view(), name="dhcp_config_entries"),
    url(r"^networks/?$", DHCPNetworksView.as_view(), name="dhcp_config_networks"),
]
