from django.conf.urls import url

from ralph.virtual.cloudsync import cloud_sync_router

urlpatterns = [
    url(
        r"^cloudsync/(?P<cloud_provider_id>\d+)/$",
        cloud_sync_router,
        name="cloud-sync-router",
    ),
]
