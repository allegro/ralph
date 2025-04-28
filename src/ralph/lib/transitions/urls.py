from django.urls import re_path

from ralph.lib.transitions.views import (
    AsyncBulkTransitionsAwaiterView,
    KillTransitionJobView,
)

urlpatterns = [
    re_path(
        r"^async-transitions-awaiter/?$",
        AsyncBulkTransitionsAwaiterView.as_view(),
        name="async_bulk_transitions_awaiter",
    ),
    re_path(
        r"^kill-transition-job/(?P<job_id>[\w\-]+)/$",
        KillTransitionJobView.as_view(),
        name="kill_transition_job",
    ),
]
