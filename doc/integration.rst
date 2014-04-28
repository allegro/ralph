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

