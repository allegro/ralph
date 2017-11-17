from django.core.checks import Error
from django.template.base import TemplateDoesNotExist
from django.template.loader import get_template


def check_transition_templates(transition_templates):
    errors = []
    if transition_templates:
        if not isinstance(transition_templates, (list, tuple)):
            errors.append(Error(
                'TRANSITION_TEMPLATES must be a list or a tuple',
                id='transitions.E001'
            ))
        else:
            for index, item in enumerate(transition_templates):
                try:
                    path, template = item
                except (ValueError, TypeError):
                    errors.append(Error(
                        'Element #{} must be a two elements tuple'.format(
                            index
                        ),
                        id='transitions.E003'
                    ))
                    continue
                try:
                    get_template(path)
                except TemplateDoesNotExist:
                    errors.append(Error(
                        'Template {} ({}) doesn\'t exist'.format(
                            template, path
                        ),
                        hint='Check TEMPLATES settings',
                        id='transitions.E002'
                    ))
    return errors
