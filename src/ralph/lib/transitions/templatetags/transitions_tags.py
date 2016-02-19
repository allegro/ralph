from django import template

register = template.Library()


@register.inclusion_tag(
    'transitions/templatetags/available_transitions.html', takes_context=True
)
def available_transitions(context, obj, field):
    """Render available transitions for instance."""
    get_available_transitions = getattr(
        obj, 'get_available_transitions_for_{}'.format(field), lambda user: []
    )
    if get_available_transitions:
        transitions = []
        for transition in get_available_transitions(user=context.request.user):
            transition.show_form = transition.has_form(obj)
            transitions.append(transition)
        context.update({
            'transitions': transitions
        })
    return context
