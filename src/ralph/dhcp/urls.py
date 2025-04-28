from django.urls import re_path

from ralph.dhcp.views import DHCPEntriesView, DHCPNetworksView, DHCPSyncView

urlpatterns = [
    re_path(r"^sync/?$", DHCPSyncView.as_view(), name="dhcp_config_sync"),
    re_path(r"^entries/?$", DHCPEntriesView.as_view(), name="dhcp_config_entries"),
    re_path(r"^networks/?$", DHCPNetworksView.as_view(), name="dhcp_config_networks"),
]
