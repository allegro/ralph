Device discovery
================

Ralph is able to automatically scan your data center and detect what hardware
is present, where it is and what software is installed on it. However, that
ability is limited to the cases covered by various discovery plugins -- if there
is a plugin for the specific kind of hardware or software -- Ralph will use it
to gather the information. If the hardware or software is not supported, you
will have to enter the information manually, in whole or in part.

Running discovery
-----------------

You can run :index:`discovery` on a specified IP address or whole network with the
"discover" management command::

    python manage.py discover '127.0.0.1'
    python manage.py discover '127.0.0.1/24'

This will attempt to invoke each of the discovery plugins on all the specified
addresses -- the plugins themselves will fill in all the information they can
gather. Some of the plugins have dependencies on other plugins, and will not
run if the plugins they depend on failed. For example, almost all plugins
depend on the "ping" plugin, so Ralph doesn't unnecessarily try to scan
addresses that are not pingable.

If you don't provide any address or networks, Ralph will attempt to scan all
the networks that it has configured.

By default, the plugins will output the results of their scanning to the
console, so you can see which ones of them worked and why the ones that didn't
work failed.

.. note::
    It is also possible to invoke discovery using the web interface's
    "Discover" tab, if you have the necessary permissions.

:index:`Remote discovery`
-------------------------

You can add the ``--remote`` parameter to the discovery command to make the
discovery happen asynchronously, done by several configured "worker" servers. Of
course, in order to do that, you need to have the worker applications started
on those servers. You do that with the command::

    python manage.py celeryd

It's possible to make some workers only process the addresses from certain
networks. The network definitions have a ``queue`` parameter which tells to
which worker queue the discovery requests should be sent. When starting a
worker you can provide a ``-Q`` parameter, to list the queues that the worker
should listen on.

Note that remote discovery will not show you the output of the plugins -- the
plugins are invoked on the workers, and not on the server where you run the
dicovery command.

It is advised to have the remote discovery command called from a cron job on
the server at least once a day, so that the information in the database is up
to date.

Plugin configuration
--------------------

Most plugins will require some configuration before they can be succesfully
used by Ralph. This is usually the login and password that they need to use
to log into whatever service they use. All that configuration should go to the
``settings-local.py`` file. 

.. warning::
    Make sure that the settings file is not readable to users who shouldn't see
    all those passwords!

You will need to have that configuration file on every worker that is supposed
to run discovery.

:index:`Import` and :index:`export`
-----------------------------------

Some information cannot be easily detected and needs to be either entered
manually through the web interface, or imported. Ralph has a number of commands
that make this easier.

You can export data from ralph in form of a CSV file by running::

    python manage.py report inventory --output=report.csv

Importing a CSV file is also easy. For example, if you have generated a
:index:`report` with the above command and changed the name and remarks of some
of the devices, you can import those changes by running::

    python manage.py --fields=id,,,,,name,,,,remarks report.csv

The ``--fields`` parameter tells which columns of the CSV file should be used
for which fields of the imported devices.

.. note::
    Data import is a potentially destructive operation. It is advices to first
    test it on a testing instance, or at least to have a complete backup of the
    database.

Ralph can also store information about :index:`DNS` and :index:`DHCP` server
settings. In order to import those, use the ``dnsimport`` and ``dhcpimport``
commands respectively.  You can export the DHCP server configuration with
``dhcpexport``. The DNS server configuration can be used directly by PowerDNS
server, if you point it to use Ralph's database.

