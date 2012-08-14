Upgrading to a newer version
============================

We release new versions of Ralph with new features and fixed bugs, so it's a
good idea to upgrade your installation when there is a new release. The upgrade
is a two-step process: first, you need to download and install new code, then
you need to migrate your database to be compatible with the new version.

Download and install new version
--------------------------------

Before you start the upgrade, you need to stop any Ralph processes that are
running -- otherwise you can get some unpredictable behavior when your files
and database are half-way through the upgrade process.

If you installed from pip, then you can simply do::

    (ralph)$ pip install --upgrade ralph
    [...]

If you installed from source, then pull in a new version and install it::

    (ralph)$ git pull
    [...]
    (ralph)$ pip install --upgrade -e .
    [...]

Either way, you need to upgrade the static files::

    (ralph)$ ralph collectstatic
    [...]


Migrate the database
--------------------

Some versions of Ralph will change the database schema in order to add or change
some of the models of the data that is stored in there. You need to migrate the
database to the current version of Ralph::

    (ralph)$ ralph syncdb
    [...]
    (ralph)$ ralph migrate
    [...]

Once your code is upgraded and the database is migrated, you can start all your Ralph processes back and enjoy the new version.

Update the settings
-------------------

Some new features added to Ralph may require additional settings to work
properly. In order to enable them in your settings, follow the instructions in
the :doc:`change log <changes>` for the version you installed. 
