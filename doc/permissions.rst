Permissions
===========

Different users can have different :index:`permissions` in Ralph. The
permissions are edited through the admin interface, in the user list. There are
two kinds of permissions: :index:`user permissions`, for direct access to the
data through the admin interface, and :index:`bound permissions`, which give
access to different parts and functionalities of the user interface.

In addition, a user who has ":index:`staff`" status will see a link to the
admin interface, while any user with the ":index:`superuser`" status will
automatically gain all possible permissions.

List of bound permissions
-------------------------

+-------------+----------------------------+-------------+
|Action [#2]_ |Object                      |Scope        |
+=============+============================+=============+
|READ         |Data center structure       |GLOBAL       |
+-------------+----------------------------+-------------+
|EDIT         |Ventures and roles          |GLOBAL       |
+-------------+----------------------------+-------------+
|CREATE+DELETE|Devices                     |GLOBAL       |
+-------------+----------------------------+-------------+
|EDIT         |Generic device info         |GLOBAL       |
+-------------+----------------------------+-------------+
|EDIT         |Financial device info       |GLOBAL       |
+-------------+----------------------------+-------------+
|EDIT         |Device support info         |GLOBAL       |
+-------------+----------------------------+-------------+
|EDIT         |DNS information             |GLOBAL       |
+-------------+----------------------------+-------------+
|ACCESS       |Discovery                   |GLOBAL       |
+-------------+----------------------------+-------------+
|READ         |Device management           |GLOBAL       |
+-------------+----------------------------+-------------+
|ACCESS       |Admin                       |GLOBAL       |
+-------------+----------------------------+-------------+
|READ         |Device group                |VENTURE [#1]_|
+-------------+----------------------------+-------------+
|READ         |Devices in a group          |VENTURE [#1]_|
+-------------+----------------------------+-------------+
|READ         |Financial device group info |VENTURE [#1]_|
+-------------+----------------------------+-------------+
|READ         |Generic device info         |VENTURE [#1]_|
+-------------+----------------------------+-------------+
|READ         |Venture and role info       |VENTURE [#1]_|
+-------------+----------------------------+-------------+
|READ         |Financial device info       |VENTURE [#1]_|
+-------------+----------------------------+-------------+
|READ         |Device support info         |VENTURE [#1]_|
+-------------+----------------------------+-------------+

.. rubric:: Footnotes

.. [#1] Results are filtered per ventures and roles the user has access to.
.. [#2] EDIT = CREATE, UPDATE and DELETE

.. _groups:

Groups
------

Instead of giving permissions to every user separately, ralph use group-based
permissions. Each group defined below represents role with defined set
of permissions. You can add users to these groups to give them access to read
and write proper part of data.

There are default groups defined:

* assets-buyer - user can view and modify assets financial data,
* assets-helper - user can modify assets assignee and localization,
* assets-staff - user has permission to manage assets data in administrator
  panel.

If you want to integrate Ralph with ldap, you will see these three metagroups
usefull:

* superuser,
* staff,
* active.

These groups are translated into ``is_GROUPNAME`` user's flags defined
in `django <https://docs.djangoproject.com/en/1.4/topics/auth/#django.contrib.auth.models.User.is_staff>`_.
Be careful of defining groups with that names, because users will be
added to them automatically after login through ldap.

:index:`API Access`
-------------------

In order for the users to be able to access the web API programmatically, they
need to have an :index:`API key` generated for them -- this can be done on the
user's page in the admin interface.

List of bound permissions
-------------------------

+----------------------+-------------------------------------+
|Resource              |Perm                                 |
+======================+=====================================+
|bladeserver           |read_dc_structure                    |
+----------------------+-------------------------------------+
|businessline          |read_configuration_item_info_generic |
+----------------------+-------------------------------------+
|ci                    |read_configuration_item_info_generic |
+----------------------+-------------------------------------+
|cichange              |read_configuration_item_info_generic |
+----------------------+-------------------------------------+
|cichangecmdbhistory   |read_configuration_item_info_generic |
+----------------------+-------------------------------------+
|cichangegit           |read_configuration_item_info_git     |
+----------------------+-------------------------------------+
|cichangepuppet        |read_configuration_item_info_puppet  |
+----------------------+-------------------------------------+
|cichangezabbixtrigger |read_configuration_item_info_generic |
+----------------------+-------------------------------------+
|cilayers              |read_configuration_item_info_generic |
+----------------------+-------------------------------------+
|ciowners              |read_configuration_item_info_generic |
+----------------------+-------------------------------------+
|cirelation            |read_configuration_item_info_generic |
+----------------------+-------------------------------------+
|citypes               |read_configuration_item_info_generic |
+----------------------+-------------------------------------+
|department            |read_dc_structure                    |
+----------------------+-------------------------------------+
|deployment            |read_deployment                      |
+----------------------+-------------------------------------+
|dev                   |read_dc_structure                    |
+----------------------+-------------------------------------+
|devicewithpricing     |read_dc_structure                    |
+----------------------+-------------------------------------+
|ipaddress             |read_network_structure               |
+----------------------+-------------------------------------+
|model                 |read_dc_structure                    |
+----------------------+-------------------------------------+
|modelgroup            |read_dc_structure                    |
+----------------------+-------------------------------------+
|physicalserver        |read_dc_structure                    |
+----------------------+-------------------------------------+
|rackserver            |read_dc_structure                    |
+----------------------+-------------------------------------+
|role                  |read_dc_structure                    |
+----------------------+-------------------------------------+
|rolelight             |read_dc_structure                    |
+----------------------+-------------------------------------+
|roleproperty          |read_dc_structure                    |
+----------------------+-------------------------------------+
|rolepropertytype      |read_dc_structure                    |
+----------------------+-------------------------------------+
|rolepropertytypevalue |read_dc_structure                    |
+----------------------+-------------------------------------+
|rolepropertyvalue     |read_dc_structure                    |
+----------------------+-------------------------------------+
|service               |read_configuration_item_info_generic |
+----------------------+-------------------------------------+
|venture               |read_dc_structure                    |
+----------------------+-------------------------------------+
|venturelight          |read_dc_structure                    |
+----------------------+-------------------------------------+
|virtualserver         |read_dc_structure                    |
+----------------------+-------------------------------------+
|global_module_access  |has_assets_access                    |
+----------------------+-------------------------------------+
|global_module_access  |has_core_access                      |
+----------------------+-------------------------------------+
|global_module_access  |has_scrooge_access                   |
+----------------------+-------------------------------------+
