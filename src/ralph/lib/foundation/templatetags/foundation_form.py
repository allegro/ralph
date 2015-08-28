from django import template

register = template.Library()


@register.inclusion_tag('foundation_form/form_label.html')
def label(field):
    """Render foundation label."""
    return {'field': field}


@register.inclusion_tag('foundation_form/form_field.html')
def field(field, is_admin=True, show_label=True):
    """Render foundation field."""
    return {
        'admin_field': field.field if is_admin else field,
        'field': field,
        'show_label': show_label
    }


@register.inclusion_tag('foundation_form/form_field.html')
def field_alone(field):
    """Render foundation field without label."""
    return {'field': field, 'show_label': False}


@register.inclusion_tag('foundation_form/form_errors.html')
def errors(form):
    """Render non field errors for a form."""
    return {'form': form}
