from collections import defaultdict

from django.core.exceptions import ObjectDoesNotExist

from ralph.admin.helpers import get_value_by_relation_path
from ralph.cross_validator.helpers import get_imported_obj, get_obj_id_ralph_20, diff
from ralph.cross_validator.models import Result, Run
from ralph.cross_validator.mappers import mappers


def _get_values(new):
    def get_value(o, path, errors):
        if o is None:
            return ''
        try:
            return get_value_by_relation_path(o, path)
        except AttributeError as e:
            errors.append(
                'AttributeError for {} and path {} ({})'.format(
                    str(o.__class__), path, str(e)
                )
            )
            return None


    values = defaultdict(dict)
    errors = []
    mapping = mappers[new.__class__]
    imported_object = get_imported_obj(new)
    old_obj_id = get_obj_id_ralph_20(imported_object)
    OldRalphModel = mapping['ralph2_model']
    old = None
    try:
        old = OldRalphModel.objects.get(id=old_obj_id)
    except ObjectDoesNotExist:
        errors.append('ObjectDoesNotExist')

    values['blacklist'] = mapping['blacklist']
    for field_name, fields_names in mapping['fields'].items():
        old_field_path, new_field_path = fields_names
        values['old'].update(
            {field_name: get_value(old, old_field_path, errors)}
        )
        values['new'].update(
            {field_name: get_value(new, new_field_path, errors)}
        )

    return values, errors


def check_objects(qs):
    run = Run.objects.create()
    invalid_count, valid_count = 0, 0
    for obj in qs:
        result, errors = check_object(obj=obj, run=run)
        if errors or bool(result):
            invalid_count += 1
        else:
            valid_count += 1
    run.invalid_count = invalid_count
    run.valid_count = valid_count
    run.save()


def check_object(obj, run=None):
    imported_object = get_imported_obj(obj)
    errors = []
    values, errors = _get_values(obj)
    diff_result = list(diff(**values))
    if run and (errors or diff_result):
        Result.create(
            run=run,
            obj=obj,
            old=imported_object,
            diff={} if 'ObjectDoesNotExist' in errors else diff_result,
            errors=errors
        )
    return diff_result, errors
