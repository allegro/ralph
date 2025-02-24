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


class HistoryForObjectNode(template.Node):
    def __init__(self, job, obj, var_name='data'):
        self.job = job
        self.obj = obj
        self.var_name = var_name

    def render(self, context):
        job = context[self.job]
        obj = context[self.obj]
        history = job.params['history_kwargs']
        context[self.var_name] = history[obj.pk].items()
        if not context[self.var_name]:
            return '&ndash;'
        return ''


@register.tag(name='history_for_object')
def history_for_object(parser, token):
    error = False
    try:
        _, job, obj, _as, var_name = token.split_contents()
        if _as != 'as':
            error = True
    except:  # noqa
        error = True

    if error:
        raise template.TemplateSyntaxError(
            'history_for_object must be of the form, "history_for_object <job> <obj> as <var_name>"'  # noqa
        )
    else:
        return HistoryForObjectNode(job, obj, var_name)
