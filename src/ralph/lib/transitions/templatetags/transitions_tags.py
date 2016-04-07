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
            transition.show_form = transition.has_form()
            transitions.append(transition)
        context.update({
            'transitions': transitions
        })
    return context


@register.filter(name='choice_str')
def choice_str(obj, field_name):
    field = obj._meta.get_field(field_name)
    value = getattr(obj, field_name)
    try:
        return field.choices.desc_from_id(value)
    except (AttributeError, ValueError):
        return value
