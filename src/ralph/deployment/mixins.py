from django.contrib import messages
from django.utils.safestring import mark_safe

from ralph.lib.transitions.models import (
    TransitionJob,
    TransitionJobActionStatus
)


def get_actions_statuses_as_html(transition):
    # TODO: sort actions
    # TODO: verbose_name
    actions_to_execute = transition.transition.actions.all()
    executed_actions = (
        transition.transition_job_actions.all()
        .order_by("created")
        .values(  # noqa
            "action_name", "status"
        )
    )

    def action_as_html(action):
        css_class = "queued"
        job_action = [a for a in executed_actions if action.name == a["action_name"]]  # noqa
        if job_action and len(job_action):
            css_class = TransitionJobActionStatus.desc_from_id(job_action[0]["status"])
        return '<span class="label small {}">{}</span>'.format(css_class, action.name)

    return " ".join([action_as_html(a) for a in actions_to_execute])


class ActiveDeploymentMessageMixin(object):
    def changeform_view(self, request, object_id, *args, **kwargs):
        current_transitions = None
        obj = self.get_object(request, object_id)
        if obj:
            current_transitions = TransitionJob.get_transitions_for_object(obj=obj)
        if current_transitions:
            current_transition = current_transitions.first()
            # TODO: separeted view
            messages.info(
                request,
                mark_safe(
                    'Transition <a href="#">{}</a> is in progress. Current status of actions: {}'.format(  # noqa
                        current_transition.transition,
                        get_actions_statuses_as_html(current_transition),
                    )
                ),
                extra_tags="static",
            )
        return super().changeform_view(request, object_id, *args, **kwargs)
