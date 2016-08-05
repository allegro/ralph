from django.conf.urls import url

from ralph.lib.transitions.views import (
    AsyncBulkTransitionsAwaiterView,
    KillTransitionJobView
)

urlpatterns = [
    url(
        r'^async-transitions-awaiter/?$',
        AsyncBulkTransitionsAwaiterView.as_view(),
        name='async_bulk_transitions_awaiter'
    ),
    url(
        r'^kill-transition-job/(?P<job_id>[\w\-]+)/$',
        KillTransitionJobView.as_view(),
        name='kill_transition_job'
    ),
]
