# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from collections import defaultdict
from functools import partial

from django.db import connection, migrations, models


def baseobject_migration(
    apps, schema_editor, app_name, model_name, rewrite_fields=None
):
    """
    Handle ids (duplication) for new BaseObject inherited model.

    Create new BaseObject instance for each old-type objects, then update
    baseobject_ptr_id to point to new BaseObject id. At the end, update all
    related models to new point to new ids.
    """
    model_str = '{}.{}'.format(app_name, model_name)
    print('Inheriting {} from baseobject'.format(model_str))
    Model = apps.get_model(app_name, model_name)
    BaseObject = apps.get_model('assets', 'BaseObject')
    ContentType = apps.get_model('contenttypes', 'ContentType')
    model_content_type = ContentType.objects.get_for_model(Model)

    id_mapping = {}
    max_id = 0
    print('Creating new IDs for {}'.format(model_str))
    for obj in Model._default_manager.order_by('baseobject_ptr_id'):
        # first of all, create new BaseObject instance for each object
        # it's id will be later referenced as baseobject_ptr_id
        base_object = BaseObject.objects.create(
            content_type=model_content_type,
            **{k: getattr(obj, v) for (k, v) in (rewrite_fields or {})}
        )
        old_pk = obj.pk
        id_mapping[old_pk] = base_object.id
        max_id = max(max_id, base_object.id)

    # increase ID of each object by
    Model._default_manager.update(
        baseobject_ptr_id=models.F('baseobject_ptr_id') + max_id
    )

    for obj in Model._default_manager.order_by('baseobject_ptr_id'):
        # use update instead of model save to call it directly in SQL without
        # Django mediation (it will try to create new object instead of updating
        # the old one)
        old_pk = obj.pk
        Model._default_manager.filter(baseobject_ptr_id=old_pk).update(
            baseobject_ptr_id=id_mapping[old_pk - max_id],
        )
        print('Mapping {} to {}'.format(old_pk, id_mapping[old_pk - max_id]))
    print(id_mapping)
    print(max_id)
    # save each obj once again to refresh content type etc
    for obj in Model._default_manager.all():
        obj.save()

    # foreign keys
    for relation in Model._meta.get_all_related_objects(local_only=True):
        related_model = relation.related_model
        relation_field = relation.field.attname
        print('Processing relation {}<->{} using field {}'.format(
            model_str, related_model, relation_field
        ))
        relation_mapping = defaultdict(list)
        for related_object in related_model._default_manager.values_list(
            'pk', relation_field
        ):
            relation_mapping[related_object[1]].append(related_object[0])
        for old_id, new_id in id_mapping.items():
            related_model._default_manager.filter(
                pk__in=relation_mapping.get(old_id, [])
            ).update(
                **{relation_field: new_id}
            )

    # TODO: m2m?


def _foreign_key_check_wrap(operations):
    db_engine = connection.vendor
    forward = reverse = None
    if db_engine == 'mysql':
        forward = 'SET foreign_key_checks=0;'
        reverse = 'SET foreign_key_checks=1;'
    # TODO: more engines

    if forward or reverse:
        operations = [
            migrations.RunSQL(forward, reverse)
        ] + operations + [
            migrations.RunSQL(reverse, forward)
        ]
    return operations


class InheritFromBaseObject(migrations.SeparateDatabaseAndState):
    """
    Handle migrating model to inherit from BaseObject.
    """
    def __init__(self, app_name, model_name, rewrite_fields=None):
        baseobject_model_migration = partial(
            baseobject_migration, app_name=app_name, model_name=model_name,
            rewrite_fields=rewrite_fields,
        )

        # state operations are separated from database operations to handle this
        # migration easily
        # state operations are later used to determine changes for futher
        # migrations (and are not applied directly on database - only on Django
        # models)
        # database operations are applied only on database (and not on Django
        # models)
        state_operations = [
            migrations.RemoveField(
                model_name=model_name.lower(),
                name='id',
            ),
            migrations.AddField(
                model_name=model_name.lower(),
                name='baseobject_ptr',
                field=models.OneToOneField(
                    auto_created=True,
                    to='assets.BaseObject',
                    serialize=False,
                    primary_key=True,
                    parent_link=True
                ),
                preserve_default=False,
            ),
        ]

        database_operations = [
            migrations.RenameField(
                model_name=model_name.lower(),
                old_name='id',
                new_name='baseobject_ptr_id'
            ),
            migrations.RunPython(
                baseobject_model_migration,
                # no need for reversing code - just keep id's as they are
                reverse_code=migrations.RunPython.noop,
            ),
        ]

        super().__init__(
            database_operations=_foreign_key_check_wrap(database_operations),
            state_operations=state_operations
        )
