import logging
from collections import defaultdict
from functools import partial

from django.core.exceptions import ObjectDoesNotExist

from ralph.admin.helpers import getattr_dunder
from ralph.cross_validator.helpers import (
    diff,
    get_imported_obj,
    get_obj_id_ralph_20
)
from ralph.cross_validator.models import CrossValidationResult

logger = logging.getLogger(__name__)


def _get_values(new, imported_object, config):
    def get_value(o, path, errors):
        if o is None:
            return ''
        return getattr_dunder(o, path)

    values = defaultdict(dict)
    errors = []
    old_obj_id = get_obj_id_ralph_20(imported_object)
    ralph2_objects = config.get(
        'ralph2_queryset', config['ralph2_model']._default_manager
    )
    old = None
    try:
        old = ralph2_objects.get(id=old_obj_id)
    except ObjectDoesNotExist:
        errors.append('ObjectDoesNotExist in Ralph2')
        return values, errors
    for error_checker in config.get('errors_checkers', []):
        error = error_checker(old, new)
        if error:
            errors.append(error)
    values['blacklist'] = config['blacklist']
    for field_name, fields in config['fields'].items():
        if callable(fields):
            if old is None:
                continue
            change_dict = fields(old, new)
            if bool(change_dict):
                values['old'].update({field_name: change_dict['old']})
                values['new'].update({field_name: change_dict['new']})
        else:
            old_field_path, new_field_path = fields
            values['old'].update(
                {field_name: get_value(old, old_field_path, errors)}
            )
            values['new'].update(
                {field_name: get_value(new, new_field_path, errors)}
            )

    return values, errors


def check_objects_of_single_type(config, run):
    invalid = valid = 0
    ralph3_objects = config.get(
        'ralph3_queryset',
        config['ralph3_model']._default_manager.all()
    )
    total = ralph3_objects.count()
    for i, obj in enumerate(ralph3_objects):
        result, errors = check_object(obj, run, config)
        if errors or bool(result):
            invalid += 1
        else:
            valid += 1

        if i % 100 == 0:
            logger.info('{} / {}'.format(i, total))

    checkers = config.get('additional_checkers', [])
    ralph2_objects = config.get(
        'ralph2_queryset', config['ralph2_model']._default_manager.all()
    )
    missing_object_callback = partial(
        missing_object_in_r3, run=run, config=config
    )
    for checker in checkers:
        checker_valid, checker_invalid = checker(
            ralph2_objects=ralph2_objects,
            ralph3_objects=ralph3_objects,
            ralph3_model=config['ralph3_model'],
            missing_object_callback=missing_object_callback
        )
        valid += checker_valid
        invalid += checker_invalid
    return valid, invalid


def missing_object_in_r3(obj, run, config):
    url = obj.get_link_to_r2()
    CrossValidationResult.create(
        run=run,
        obj=config['ralph3_model'](),
        old=None,
        diff={},
        errors=['Missing object <a href="{}">{}</a> in Ralph3'.format(
            url, str(obj)
        )],
    )


def check_object(obj, run, config):
    imported_object = get_imported_obj(obj)
    errors = []
    values, errors = _get_values(obj, imported_object, config)
    if values:
        diff_result = list(diff(**values))
    else:
        diff_result = {}
    if run and (errors or diff_result):
        CrossValidationResult.create(
            run=run,
            obj=obj,
            old=imported_object,
            diff={} if 'ObjectDoesNotExist' in errors else diff_result,
            errors=errors
        )
    return diff_result, errors
