from django import template

register = template.Library()


@register.inclusion_tag(
    'transitions/templatetags/available_transitions.html', takes_context=True
)
def available_transitions(context, obj, field):
    """Render available transitions for instance."""
    get_available_transitions = getattr(
        obj, 'get_available_transitions_for_{}'.format(field), None
    )
    if get_available_transitions:
        context.update({'transitions': get_available_transitions()})
    return context
