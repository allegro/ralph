# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
from collections import defaultdict
from contextlib import ContextDecorator
from functools import partial

from django.db import connection, migrations, models
from django.db.backends.base.schema import _related_non_m2m_objects

logger = logging.getLogger(__name__)


def baseobject_migration(
    apps, schema_editor, app_name, model_name, rewrite_fields=None
):
    """
    Handle ids (duplication) for new BaseObject inherited model.

    Create new BaseObject instance for each old-type objects, then update
    baseobject_ptr_id to point to new BaseObject id. At the end, update all
    related models to new point to new ids.
    """
    model_str = "{}.{}".format(app_name, model_name)
    logger.info("Inheriting {} from baseobject".format(model_str))
    Model = apps.get_model(app_name, model_name)
    BaseObject = apps.get_model("assets", "BaseObject")
    ContentType = apps.get_model("contenttypes", "ContentType")
    model_content_type = ContentType.objects.get_for_model(Model)

    id_mapping = {}
    max_id = 0
    logger.info("Creating new IDs for {}".format(model_str))
    for obj in Model._default_manager.order_by("baseobject_ptr_id"):
        # first of all, create new BaseObject instance for each object
        # it's id will be later referenced as baseobject_ptr_id
        base_object = BaseObject.objects.create(
            content_type_id=model_content_type.id,
            **{k: getattr(obj, v) for (k, v) in (rewrite_fields or {}).items()},
        )
        old_pk = obj.pk
        id_mapping[old_pk] = base_object.id
        max_id = max(max_id, base_object.id)

    # increase ID of each object by
    Model._default_manager.update(
        baseobject_ptr_id=models.F("baseobject_ptr_id") + max_id
    )

    for obj in Model._default_manager.order_by("baseobject_ptr_id"):
        # use update instead of model save to call it directly in SQL without
        # Django mediation (it will try to create new object instead of updating
        # the old one)
        old_pk = obj.pk
        Model._default_manager.filter(baseobject_ptr_id=old_pk).update(
            baseobject_ptr_id=id_mapping[old_pk - max_id],
        )
        logger.info("Mapping {} to {}".format(old_pk, id_mapping[old_pk - max_id]))

    # save each obj once again to refresh content type etc
    for obj in Model._default_manager.all():
        obj.save()

    # foreign keys
    # migrated from deprecated get_all_related_objects(local_only=True)
    for relation in Model._meta.get_fields(include_parents=False):
        if (
            (relation.one_to_many or relation.one_to_one)
            and relation.auto_created
            and not relation.concrete
        ):
            related_model = relation.related_model
            relation_field = relation.field.attname
            logger.info(
                "Processing relation {}<->{} using field {}".format(
                    model_str, related_model, relation_field
                )
            )
            relation_mapping = defaultdict(list)
            for related_object in related_model._default_manager.values_list(
                "pk", relation_field
            ):
                relation_mapping[related_object[1]].append(related_object[0])
            for old_id, new_id in id_mapping.items():
                related_model._default_manager.filter(
                    pk__in=relation_mapping.get(old_id, [])
                ).update(**{relation_field: new_id})

    # ImportedObjects
    ImportedObjects = apps.get_model("data_importer", "ImportedObjects")
    for old_id, new_id in id_mapping.items():
        ImportedObjects._default_manager.filter(
            object_pk=old_id,
            content_type=model_content_type,
        ).update(object_pk=new_id)

    # TODO: m2m?


def _foreign_key_check_wrap(operations):
    db_engine = connection.vendor
    forward = reverse = None
    if db_engine == "mysql":
        forward = "SET foreign_key_checks=0;"
        reverse = "SET foreign_key_checks=1;"
    # TODO: more engines

    if forward or reverse:
        operations = (
            [migrations.RunSQL(forward, reverse)]
            + operations
            + [migrations.RunSQL(reverse, forward)]
        )
    return operations


class DropAndCreateForeignKey(ContextDecorator):
    """
    Drop FK to old_field before migration operation and recreate FK (to the new
    field) after migration operation.
    """

    def __init__(self, old_field, new_field, schema_editor):
        self.old_field = old_field
        self.new_field = new_field
        self.schema_editor = schema_editor

    def __enter__(self):
        # copy from django.db.backends.base.schema.BaseDatabaseSchemaEditor._alter_field  # noqa
        # drop any FK pointing to old_field
        for _old_rel, new_rel in _related_non_m2m_objects(
            self.old_field, self.new_field
        ):
            rel_fk_names = self.schema_editor._constraint_names(
                new_rel.related_model, [new_rel.field.column], foreign_key=True
            )
            for fk_name in rel_fk_names:
                logger.debug("Dropping FK to {} ({})".format(new_rel.field, fk_name))
                self.schema_editor.execute(
                    self.schema_editor._delete_constraint_sql(
                        self.schema_editor.sql_delete_fk, new_rel.related_model, fk_name
                    )
                )

    def __exit__(self, *exc):
        # copy from django.db.backends.base.schema.BaseDatabaseSchemaEditor._alter_field  # noqa
        # (re)create any FK pointing to the new field
        for rel in self.new_field.model._meta.related_objects:
            if not rel.many_to_many:
                logger.debug("Recreating FK to {}".format(rel.field))
                self.schema_editor.execute(
                    self.schema_editor._create_fk_sql(
                        rel.related_model, rel.field, "_fk"
                    )
                )


class RenameFieldWithFKDrop(migrations.RenameField):
    """
    Rename field with dropping any FK pointing to it before actual renaming
    and recreating them after renaming.

    It's especially usefull for MySQL 5.5, where renaming field that is
    referenced by another table is not supported (errno 150). The workaround
    here is to drop FK first, then rename field, and then recreate FK. It's
    supported fully since MySQL 5.6.6.

    Resources:
    https://code.djangoproject.com/ticket/24995
    https://github.com/django/django/pull/4881
    http://dev.mysql.com/doc/refman/5.5/en/create-table-foreign-keys.html
    http://stackoverflow.com/questions/2014498/renaming-foreign-key-columns-in-mysql  # noqa
    """

    def database_forwards(self, app_label, schema_editor, from_state, to_state):
        to_model = to_state.apps.get_model(app_label, self.model_name)
        if self.allow_migrate_model(schema_editor.connection.alias, to_model):
            from_model = from_state.apps.get_model(app_label, self.model_name)
            old_field = from_model._meta.get_field(self.old_name)
            new_field = to_model._meta.get_field(self.new_name)
            with DropAndCreateForeignKey(old_field, new_field, schema_editor):
                schema_editor.alter_field(from_model, old_field, new_field)

    def database_backwards(self, app_label, schema_editor, from_state, to_state):
        to_model = to_state.apps.get_model(app_label, self.model_name)
        if self.allow_migrate_model(schema_editor.connection.alias, to_model):
            from_model = from_state.apps.get_model(app_label, self.model_name)
            old_field = from_model._meta.get_field(self.new_name)
            new_field = to_model._meta.get_field(self.old_name)
            with DropAndCreateForeignKey(old_field, new_field, schema_editor):
                schema_editor.alter_field(from_model, old_field, new_field)


class InheritFromBaseObject(migrations.SeparateDatabaseAndState):
    """
    Handle migrating model to inherit from BaseObject.
    """

    def __init__(self, app_name, model_name, rewrite_fields=None):
        baseobject_model_migration = partial(
            baseobject_migration,
            app_name=app_name,
            model_name=model_name,
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
                name="id",
            ),
            migrations.AddField(
                model_name=model_name.lower(),
                name="baseobject_ptr",
                field=models.OneToOneField(
                    auto_created=True,
                    to="assets.BaseObject",
                    serialize=False,
                    primary_key=True,
                    parent_link=True,
                    on_delete=models.CASCADE,
                ),
                preserve_default=False,
            ),
        ]

        database_operations = [
            RenameFieldWithFKDrop(
                model_name=model_name.lower(),
                old_name="id",
                new_name="baseobject_ptr_id",
            ),
            migrations.RunPython(
                baseobject_model_migration,
                # no need for reversing code - just keep id's as they are
                reverse_code=migrations.RunPython.noop,
            ),
        ]

        super().__init__(
            database_operations=_foreign_key_check_wrap(database_operations),
            state_operations=state_operations,
        )
