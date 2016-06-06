from django.conf.urls import url

from ralph.lib.transitions.views import AsyncBulkTransitionsAwaiterView

urlpatterns = [
    url(
        r'^async-transitions-awaiter/?$',
        AsyncBulkTransitionsAwaiterView.as_view(),
        name='async_bulk_transitions_awaiter'
    ),
]
