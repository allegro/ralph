import logging

from django.core.checks import Error
from django.db.utils import DatabaseError
from django.template.loader import get_template, TemplateDoesNotExist

logger = logging.getLogger(__name__)


def check_transition_templates(transition_templates):
    # to prevent AppRegistryNotReady
    from ralph.lib.transitions.models import Transition

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
                        hint='Check TRANSITION_TEMPLATES settings',
                        id='transitions.E002'
                    ))
    excluded_templates = ['']
    if transition_templates:
        try:
            excluded_templates.extend(
                {template for template, _ in transition_templates}
            )
        except ValueError:
            pass
    transitions_with_custom_templates = Transition.objects.exclude(
        template_name__in=excluded_templates
    )
    try:
        for transition in transitions_with_custom_templates:
            errors.append(Error(
                'Template {} for {} transition is '
                'defined only in transition'.format(
                    transition.template_name, transition
                ),
                hint=(
                    'Change your TRANSITION_TEMPLATES settings by adding'
                    ' ({}, "Your template name") and then '
                    'edit {} transition').format(
                        transition.template_name, transition
                ),
                id='transitions.E004'
            ))
    except DatabaseError as e:
        logger.error(e)
    return errors
