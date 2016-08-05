from django.contrib import messages
from django.utils.safestring import mark_safe

from ralph.lib.transitions.models import TransitionJob


class ActiveDeploymentMessageMixin(object):
    def changeform_view(self, request, object_id, *args, **kwargs):
        obj = self.get_object(request, object_id)
        current_transitions = TransitionJob.get_transitions_for_object(
            obj=obj, only_active=True
        )
        if current_transitions:
            current_transition = current_transitions.first()
            messages.info(request, mark_safe(
                'Transition <a href="#">{}</a> is in progress. {}'.format(
                    current_transition.transition,
                    [a.name for a in current_transition.transition.actions.all()]
                )
            ))
        return super().changeform_view(request, object_id, *args, **kwargs)
