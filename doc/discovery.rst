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

    (ralph)$ ralph discover '127.0.0.1'
    (ralph)$ ralph discover '127.0.0.1/24'

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

    (ralph)$ ralph celeryd

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

    (ralph)$ ralph report inventory --output=report.csv

Importing a CSV file is also easy. For example, if you have generated a
:index:`report` with the above command and changed the name and remarks of some
of the devices, you can import those changes by running::

    (ralph)$ ralph import --fields=id,,,,,name,,,,remarks report.csv

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

Discovery plugins
-----------------

Ralph comes with a number of discovery plugins built in. Some of them are
necessary for discovery to function, others can be safely skipped.

Ping Plugin
~~~~~~~~~~~~

This plugin requires no additional settings. It will ping the specified IP
address to check whether it is available. Most discovery plugins will not run
if this plugin failed. This plugin doesn't create any devices in the database.


HTTP Plugin
~~~~~~~~~~~

This plugin will attempt to connect to ports 80 and 443 of the specified IP
address and try to get a page using HTTP or HTTPS, respectively. Then it will
parse its response headers and body content, and attempt to guess the vendor
and model of the device in question, using a number of hard-coded heuristics.
This plugin doesn't require any configuration. This plugin doesn't create any
devices in the database.


SNMP Plugin
~~~~~~~~~~~

This plugin will try to connect to the specified IP address through the SNMP
protocol, and retrieve its System Name property. To function properly, this
plugin needs to know the list of SNMP communities to try, which you set in the
``SNMP_PLUGIN_COMMUNITIES`` variable. Optionally, this plugin can also attempt
to use SNMP version 3 -- then it also needs ``SNMP_V3_USER``,
``SNMP_V3_AUTH_KEY`` and ``SNMP_V3_PRIV_KEY`` set. This plugin doesn't create
any devices in the database, but collects information that is later used by
many other plugins.


SNMP MAC Plugin
~~~~~~~~~~~~~~~

This plugin will attempt to get the list of device's MAC hardware addresses
through the SNMP protocol. In addition, it may be able to retrieve the model
name and serial number for some models of devices. It doesn't require any
additional configuration, apart from that already done for the ``SNMP Plugin``.
If it retrieves the MAC addresses or a serial number, it will create a device
in Ralph's database.


IPMI Plugin
~~~~~~~~~~~

This plugin will try to connect to the specified IP using the IPMI protocol,
and attempt to retrieve information about the device's vendor, model, serial
number, MAC addresses and hardware components. If it succeeds, it creates a
corresponding device in the Ralph's database. For proper operation this plugin
requires a ``ipmitool`` binary to be installed, and the ``IPMI_USER`` and
``IPMI_PASSWORD`` settings variables set.


HTTP Supermicro Plugin
~~~~~~~~~~~~~~~~~~~~~~

This plugin will attempt to log into the web interface of a Supermicro server
management, and scrap the information about its hardware MAC addresses. If
successful, it will create a corresponding device in Ralph's database. It will
use the same credentials as the ``IPMI Plugin``.


SSH Linux Plugin
~~~~~~~~~~~~~~~~

This plugin will attempt to connect to the specified IP address using SSH, log
into the configured user account and retrieve information about the device's
hardware using common linux commands. This plugin requires that the remote
system allows logging in using the ``SSH_USER`` and ``SSH_PASSWORD`` or
``XEN_USER`` and ``XEN_PASSWORD`` as credentials. It also requires that this
user is allowed to run ``sudo dmidecode``, ``ip``, ``hostname``, ``uname``,
``df`` and read ``/proc/meminfo`` and ``/proc/cpuinfo``. If the plugin manages
to retrieve the MAC addresses or device's serial number, it creates a
corresponding entry in Ralph's database.


SSH Proxmox Plugin
~~~~~~~~~~~~~~~~~~

This plugin will attempt to connect to the specified IP address using SSH, log
into the root account using configured ``SSH_PASSWORD`` and retrieve
information about the virtual servers running in a Proxmox cluster on this
server. It will add the information about those virtual servers to the Ralph's
database.


SSH XEN Plugin
~~~~~~~~~~~~~~~~~~

This plugin will attempt to connect to the specified IP address using SSH, log
into it configured ``XEN_USER`` and ``XEN_PASSWORD`` and retrieve information
about the virtual servers running in a XEN cluster on this server. It will add
the information about those virtual servers to the Ralph's database. For this
plugin to work correctly, the server needs to have the account configured to
allow login and executing of the following commands::

    sudo xe vif-list params=vm-name-label,MAC
    sudo xe vm-disk-list vdi-params=sr-uuid,uuid,virtual-size vbd-params=vm-name-label,type,device 
    sudo xe sr-list params=uuid,physical-size,type
    sudo xe vm-list params=uuid,name-label,power-state,VCPUs-number,memory-actual


SSH Ganeti Plugin
~~~~~~~~~~~~~~~~~

This plugin will attempt to connect to the specified IP address using SSH, log
into it configured ``SSH_USER`` and ``SSH_PASSWORD`` and retrieve information
about the virtual servers running in a Ganeti cluster on this server. It will
add the information about those virtual servers to the Ralph's database.




Integration with external services
----------------------------------

Ralph can communicate with some external services.

OpenStack
~~~~~~~~~

If you configure the variables ``OPENSTACK_URL``, ``OPENSTACK_USER`` and
``OPENSTACK_PASSWORD`` to point to the nova API of your OpenStack instance,
then you can use the command::

    (ralph)$ ralph openstack

to pull in the billing information for OpenStack tennants for the previous day.
New "openstack" components will be then created in the catalog, where you can
set the prices for them.  That information is then displayed in the "Venture"
tab summary.

You can add an optional ``--remote`` parameter to make the command run on any
celery worker that listens on the ``openstack`` queue.

Zabbix
~~~~~~

If you configure ``ZABBIX_URL``, ``ZABBIX_USER`` and ``ZABBIX_PASSWORD``, with
the addition of ``ZABBIX_DEFAULT_GROUP``, then you can use the command::

    (ralph)$ ralph zabbixregister

to automatically create Zabbix hosts and host templates for all the devices
that have a zabbix integration "template" variable set in their roles.

You can add an optional ``--remote`` parameter to make the command run on any
celery worker that listens on the ``zabbix`` queue.

Splunk
~~~~~~

If you configure ``SPLUNK_URL``, ``SPLUNK_USER`` and ``SPLUNK_PASSWORD``, then
you can use the command::

    (ralph)$ ralph splunk

to download usage information about all the hosts from Splunk. New components
will be created in the catalog, where you can set their prices. That
information is then displayed in the "Venture" tab summary.

