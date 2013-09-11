DNS configuration
*****************

The way Ralph stores and manipulates the information about domain names in its
database is compatible with the way the PowerDNS daemon does it -- so you can
just point an instance of PowerDNS to Ralph's database and have all changes
done through Ralph immediately reflected in PowerDNS configuration.

Importing configuration
=======================

Ralph also has a command for importing a zone file into its database, so that
you can migrate your existing DNS configuration easily::

    ralph dnsimport <filename>

Note, that this command is not suitable for updating an existing zone
configuration -- it's only good for creating a new zone.
