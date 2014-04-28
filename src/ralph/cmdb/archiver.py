#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.db import connection
from lck.django.common import nested_commit_on_success

from ralph.cmdb.models import (
    ArchivedCIChange,
    ArchivedCIChangeCMDBHistory,
    ArchivedCIChangeGit,
    ArchivedCIChangePuppet,
    ArchivedCIChangeZabbixTrigger,
    ArchivedPuppetLog,
    CI_CHANGE_TYPES,
    CIChange,
    CIChangeCMDBHistory,
    CIChangeGit,
    CIChangePuppet,
    CIChangeZabbixTrigger,
    PuppetLog,
)


def _get_used_db_backend_name():
    """
    Return used database backend name or None.
    """
    cursor = connection.cursor()
    backend_str = str(cursor.db).lower()
    # `ENGINE` part of database configuration is substring
    # of string representation for `cursor.db` object
    if 'mysql' in backend_str:
        return 'mysql'
    elif 'postgresql' in backend_str:
        return 'postgresql'
    elif 'sqlite' in backend_str:
        return 'sqlite'


def _get_db_columns_for_model(model):
    """
    Return list of columns names for passed model.
    """
    return [field.column for field in model._meta._fields()]


def _get_db_table_for_model(model):
    """
    Return table name in database server for passed model.
    """
    return model._meta.db_table


def _make_base_insert_query(model, archived_model):
    """
    Create moved data SQL query with simple conditions.
    """
    db_columns = _get_db_columns_for_model(model)
    sql = """
        INSERT INTO {archived_table_name} ({columns})
        SELECT {columns} FROM {table_name}
        WHERE created<=%s AND type=%s
    """.format(
        archived_table_name=_get_db_table_for_model(archived_model),
        columns=','.join(db_columns),
        table_name=_get_db_table_for_model(model),
    )
    return sql.strip()


def _make_advanced_insert_query(
    model,
    archived_model,
    joined_model,
    join_by=('id', 'object_id'),
):
    """
    Create not trivial moved data SQL query with advanced conditions.
    Not trivial means that we have two linked tables and we should move data
    using `JOIN` syntax.
    """
    db_columns = _get_db_columns_for_model(model)
    first_table_name = _get_db_table_for_model(model)
    sql = """
        INSERT INTO {archived_table_name} ({columns})
        SELECT {source_columns}
        FROM {first_table_name} JOIN {second_table_name}
            ON {second_table_name}.{r_id}={first_table_name}.{l_id}
        WHERE
            {second_table_name}.created<=%s AND
            {second_table_name}.type=%s
    """.format(
        archived_table_name=_get_db_table_for_model(archived_model),
        columns=','.join(db_columns),
        source_columns=','.join([
            '`%s`.`%s`' % (first_table_name, col) for col in db_columns
        ]),
        first_table_name=first_table_name,
        second_table_name=_get_db_table_for_model(joined_model),
        l_id=join_by[0],
        r_id=join_by[1],
    )
    return sql.strip()


def _make_base_delete_query(model):
    """
    Create simple delete query.
    """
    return 'DELETE FROM {} WHERE created<=%s AND type=%s'.format(
        _get_db_table_for_model(model),
    )


def _make_advanced_delete_query(
    model,
    joined_model,
    join_by=('id', 'object_id'),
):
    """
    Create advanced delete query with not trivial conditions.
    Not trivial means that we have two linked tables and we should
    delete (if db backend have this possibility) data using `JOIN` syntax.
    """
    backend_name = _get_used_db_backend_name()
    if backend_name == 'mysql':
        sql = """
            DELETE {first_table_name}.* FROM {first_table_name}
            JOIN {second_table_name}
                ON {second_table_name}.{r_id}={first_table_name}.{l_id}
            WHERE
                {second_table_name}.created<=%s AND
                {second_table_name}.type=%s
        """
    elif backend_name == 'postgresql':
        sql = """
            DELETE FROM {first_table_name}
            USING {second_table_name}
            WHERE
                {second_table_name}.{r_id}={first_table_name}.{l_id}
                AND {second_table_name}.created<=%s
                AND {second_table_name}.type=%s
        """
    else:
        sql = """
            DELETE FROM {first_table_name}
            WHERE {first_table_name}.{l_id} IN (
                SELECT {second_table_name}.{r_id}
                FROM {second_table_name}
                WHERE
                    {second_table_name}.created<=%s AND
                    {second_table_name}.type=%s
            )
        """
    return sql.format(
        first_table_name=_get_db_table_for_model(model),
        second_table_name=_get_db_table_for_model(joined_model),
        l_id=join_by[0],
        r_id=join_by[1],
    ).strip()


def _get_query_params_list(older_than, change_type):
    """
    Create a formatted params list.
    """
    return [
        older_than.strftime('%Y-%m-%d %H:%M:%S'),
        int(change_type),
    ]


def _run_archivization(
    model,
    archived_model,
    older_than,
    change_type,
    parent_model=None
):
    """
    Execute archivization process for data older than `older_than`, which type
    is specified in `change_type` variable. If `parent_model` is passed it
    will be used to make `WHERE` conditions. Otherwise conditions are
    build on `model` variable.

    :param model: The archived model
    :param archived_model: Model to store archived data
    :param older_than: Query condition
    :param change_type: Query condition
    :param parent_model: Empty or model to construct `WHERE` conditions.
        This model is connected with archived model with a foreign key.
    """
    cursor = connection.cursor()
    if not parent_model:
        sql = _make_base_insert_query(model, archived_model)
    else:
        sql = _make_advanced_insert_query(model, archived_model, parent_model)
    params = _get_query_params_list(older_than, change_type)
    cursor.execute(sql, params)


def _remove_old_data(model, older_than, change_type, parent_model=None):
    """
    Remove data older than `older_than`, which type is specified
    in `change_type` variable. If parent_model is passed it will be used to
    make `WHERE` conditions. Otherwise conditions are build on `model`
    variable.

    :param model: The archived model
    :param older_than: Query condition
    :param change_type: Query condition
    :param parent_model: Empty or model to construct `WHERE` conditions.
        This model is connected with archived model with a foreign key.
    """
    cursor = connection.cursor()
    if not parent_model:
        sql = _make_base_delete_query(model)
    else:
        sql = _make_advanced_delete_query(model, parent_model)
    params = _get_query_params_list(older_than, change_type)
    cursor.execute(sql, params)


@nested_commit_on_success
def run_cichange_git_archivization(older_than):
    _run_archivization(
        CIChange,
        ArchivedCIChange,
        older_than,
        CI_CHANGE_TYPES.CONF_GIT,
    )
    _run_archivization(
        CIChangeGit,
        ArchivedCIChangeGit,
        older_than,
        CI_CHANGE_TYPES.CONF_GIT,
        parent_model=CIChange,
    )
    _remove_old_data(
        CIChangeGit,
        older_than,
        CI_CHANGE_TYPES.CONF_GIT,
        parent_model=CIChange,
    )
    _remove_old_data(
        CIChange,
        older_than,
        CI_CHANGE_TYPES.CONF_GIT,
    )


@nested_commit_on_success
def run_cichange_zabbix_archivization(older_than):
    _run_archivization(
        CIChange,
        ArchivedCIChange,
        older_than,
        CI_CHANGE_TYPES.ZABBIX_TRIGGER,
    )
    _run_archivization(
        CIChangeZabbixTrigger,
        ArchivedCIChangeZabbixTrigger,
        older_than,
        CI_CHANGE_TYPES.ZABBIX_TRIGGER,
        parent_model=CIChange,
    )
    _remove_old_data(
        CIChangeZabbixTrigger,
        older_than,
        CI_CHANGE_TYPES.ZABBIX_TRIGGER,
        parent_model=CIChange
    )
    _remove_old_data(
        CIChange,
        older_than,
        CI_CHANGE_TYPES.ZABBIX_TRIGGER,
    )


@nested_commit_on_success
def run_cichange_cmdb_history_archivization(older_than):
    _run_archivization(
        CIChange,
        ArchivedCIChange,
        older_than,
        CI_CHANGE_TYPES.CI,
    )
    _run_archivization(
        CIChangeCMDBHistory,
        ArchivedCIChangeCMDBHistory,
        older_than,
        CI_CHANGE_TYPES.CI,
        parent_model=CIChange,
    )
    _remove_old_data(
        CIChangeCMDBHistory,
        older_than,
        CI_CHANGE_TYPES.CI,
        parent_model=CIChange,
    )
    _remove_old_data(
        CIChange,
        older_than,
        CI_CHANGE_TYPES.CI,
    )


@nested_commit_on_success
def run_cichange_device_archivization(older_than):
    _run_archivization(
        CIChange,
        ArchivedCIChange,
        older_than,
        CI_CHANGE_TYPES.DEVICE,
    )
    _remove_old_data(
        CIChange,
        older_than,
        CI_CHANGE_TYPES.DEVICE,
    )


@nested_commit_on_success
def run_cichange_puppet_archivization(older_than):
    _run_archivization(
        CIChange,
        ArchivedCIChange,
        older_than,
        CI_CHANGE_TYPES.CONF_AGENT,
    )
    _run_archivization(
        CIChangePuppet,
        ArchivedCIChangePuppet,
        older_than,
        CI_CHANGE_TYPES.CONF_AGENT,
        parent_model=CIChange,
    )
    cursor = connection.cursor()
    params = _get_query_params_list(older_than, CI_CHANGE_TYPES.CONF_AGENT)
    sql = _make_advanced_insert_query(
        PuppetLog,
        ArchivedPuppetLog,
        CIChange,
        join_by=('cichange_id', 'object_id'),
    )
    cursor.execute(sql, params)
    sql = _make_advanced_delete_query(
        PuppetLog,
        CIChange,
        join_by=('cichange_id', 'object_id'),
    )
    cursor.execute(sql, params)
    _remove_old_data(
        CIChangePuppet,
        older_than,
        CI_CHANGE_TYPES.CONF_AGENT,
        parent_model=CIChange,
    )
    _remove_old_data(
        CIChange,
        older_than,
        CI_CHANGE_TYPES.CONF_AGENT,
    )
