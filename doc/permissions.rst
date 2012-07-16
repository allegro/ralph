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

Groups
------

Instead of giving permissions to every user separately, you can instead create
a group with a specific set of permissions, and add those users to this group.
The groups are also edited in the admin interface.

:index:`API Access`
-------------------

In order for the users to be able to access the web API programmatically, they
need to have an :index:`API key` generated for them -- this can be done on the
user's page in the admin interface.
