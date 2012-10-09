Change Log
----------

1.1.2
~~~~~

Released on October 8, 2012.

* ``Donpedro`` introduced: a new dedicated discovery agent for Windows.  Works
  as a background Windows service; a lightweight alternative to SCCM

* a new plugin to discover Xen hypervisors (with support for information about
  pools and hardware usage)

* a new ``ssh_linux`` plugin that discovers Linux machines by logging into them;
  an alternative to Puppet storeconfig

* lots of minor bugfixes in UI, CMDB and discovery

1.1.1
~~~~~

Released on September 24, 2012.

* Price catalog updated: history of changes tracked, a more intuitive UI for
  prices per unit of size

* bug fixes in discovery and UI

1.1.0
~~~~~

Released on September 19, 2012.

* Deployment of new machines using PXE implemented

* CMDB: change acceptance

* DHCP can be served and reconfigured remotely

* Improved reports: new report types for devices, main menu entry for generic
  reports, a details view for devices in reports

* API supports throttling

* A new component kind, ``OperatingSystem``, with information about CPU, memory
  and disk storage visible from the operating system

* Operating system components included in pricing

* OpenStack pricing now includes pricing margins

* Extra costs are now a dictionary

* Improved date pickers in UI

1.0.6
~~~~~

Released on August 20, 2012.

* Pricing: cached prices updated after changes in the catalog; component price
  calculation includes custom sizes when relevant

* ``ralph`` commands no longer display the unhelpful "Error opening file for
  reading: Permission denied" message

* Usability improvements in editing CI relations

* Preliminary timeline view for CMDB added

* Git configuration change from Puppet agent now knows if a change was
  successful

* minor bugfixes

1.0.5
~~~~~

Released on August 13, 2012.

* OpenStack plugin now accepts OPENSTACK_EXTRA_QUERIES setting, containing a
  list of tuples in the form (url, query) of additional data sources to check.

* make the discovery plugins use soft delete

* the proxmox discovery plugin now counts local storage used

* added a "delete" link in the addresses view

* positions in racks are now numbered from the bottom

* CMDB: enabled removing relations, faster git handling

* bugfixes in CMDB and UI code

1.0.4
~~~~~

Released on August 08, 2012.

* edit links for devices and components

* soft-deletable devices

* a view showing physical layout of racks

* add a filter form in the networks view

* small usability improvements in the history user interface

* added a "zabbixregister" command for automatically creating hosts and
  host templates in Zabbix

* bugfixes in the CMDB

* bugfixes in the discovery plugins

1.0.3 
~~~~~

Released on August 01, 2012.

* a rudimentary reports tab on device lists to filter devices according to
  specified rules

* venture tree collapsible

* CMDB integration scripts integrated into framework 

* CMDB supports distributed plugins

* minor fixes in the Web app  

1.0.2
~~~~~

Released on July 23, 2012.

* ``ralph chains`` command to list available plug-in chains

* fixed regression from 1.0.1: ``settings-local.py`` works correctly again

* ability to create new devices from the web application

* several minor bugfixes

* added cmdb charts for dashboard

1.0.1
~~~~~

Released on July 18, 2012.

* ``ralph`` management command introduced as a shortcut to ``python manage.py``

* ``ralph makeconf`` management command introduced to create configuration from
  a template

* PyPI package fixed by including all resources in the source package

* minor fixes for the SQLite backend

* minor documentation fixes and updates

1.0.0
~~~~~

Released on July 16, 2012.

* initial release
