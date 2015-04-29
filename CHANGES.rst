Change Log
----------

2.3.1
~~~~~

Released on April 23, 2015

New features
************
* Changed default STATICFILES_STORAGE to cached.
* Moved visualization to new section (DC view).
* Added networks to top menu with option to hide it (HIDE_MENU setting).
* Added mechanism generating demo data as CLI command.


Fixes
*****
* Fixed getting name of default pool for load balancers.
* Transactional save on scan form.
* Removed lck.activitylog from Ralph.
* Fixed unicode error and empty country by default in LDAP login.


2.3.0
~~~~~

Released on April 13, 2015

New features
************
* Added data center and racks visualization.
* Ralph requires ralph_assets package.
* Improved Xen detection.
* Better ssh communication with cisco switches.
* Added possibility to store databases in Ralph and better support for storing load balancers virtual servers.
* Updated docs for Don Pedro agent and Ralph's installation process.
* We've moved documentation to the rtd: http://ralph.readthedocs.org/en/latest/.
* Docker is the official way to easy install Ralph.


Minor improvements
******************
* SCAN:
    - Detaching logical subdevices not found by scan: Previously only physical subdevices not found by scan were detached. Extended this feature on logical children.
    - Detect Dell family in scan, when headers not contains `Server`
    - Puppet-plugin: added expanduser call on cert paths.
    - Puppet plugin can get data from puppetdb-api.
    - 'Force autoscan' is now triggered only when SNMP name is missing.
* DEPLOY:
    - Added two missing features to deploy/clean plugin: The hostname is now copied from deployment and copying venture/role from deployment.
    - Changed the required permission for VM creation - You need core access to create a VM via API.
    - Added new entry point to API to provide possibility to change IP address after deployment.
* GUI:
    - Added management IP in 'Addresses' tab (device view).
    - Scan form - now it's possible to add some new components to the existing device.
* CMDB:
    - Set CI.state default value to ACTIVE.
* OTHER:
    - The design of top bar is now in line with the Scrooge UI.
    - Scrooge API: Databases and Load balancer virtual servers added.
    - Added department to search form.
    - Functionality to inject custom tracking code.
    - Admin panel: changing management and management ip addresses blocked.
    - `ralph makeconf` set pluggable apps to the reasonable defaults.
    - For devices with assigned Asset (only without is_blade flag) it is no longer possible to change position.
    - You can now set user's country using LDAP attribute.
    - Added Powerdns Record resource to REST API.

Fixes
*****
* Fix for MAC detecting in IDRAC plugin.
* Parent and management fields are now readonly when an asset is assigned. Before this change we could't save form.
* Updated parse_lshw(..) to work with puppetdb_api. Used better msg when no facts found.
* Fixed docker installation.
* Scan form now creates IPAddress object when does not exist.

2.1.0
~~~~~

Released on October 14, 2014

This version contains huge code clean-ups (some really old parts were removed), several bugfixes, slightly redesigned UI, improved integration with other componenets (i.e. Assets, Scrooge) and some new features as well (concepts of 'Services' and 'Environments', 'Pending Changes' view, detection of network connections between devices via LLDP).

* CORE: Added service/environment validation to device editing/creating forms.

* CORE: Fixes for displaying device's components and changes for 'parts' in scan results.

* CORE: Fix for propagating changes of parent rack/dc.

* CORE: Improved checks for required asset.

* CORE: 'Services' view added.

* CORE: Fix for 'Home Page' option in user's preferences view.

* CORE: Network connections detected via LLDP.

* CORE: Improved handling of assets that should be linked to devices.

* CORE: Improved handling of ventures that shouldn't be shown in Ralph.

* CORE: Improvements for the GUI.

* CORE: Added search fields for 'service catalog' and 'device environment'.

* CORE: Removed significant parts of obsolete code.

* CORE: After sign in, redirect to home of user-accessible module.

* CORE: Improved deployment API.

* SCAN: Better changes detection.

* SCAN: Improved handling of blacklisted serial numbers.

* SCAN: Scan status view.

* CMDB: API shows more data.

2.0.1
~~~~~

Released on August 20, 2014

This is a bugfix release, with some small improvements here and there and one new feature ('notifications' module).

* CORE: (CI/Travis/Coveralls) Added Sphinx checker.

* SCAN: Small fix for the 'force autoscan' routine.

* SCAN: Improved detection of Juniper switches.

* CORE: Added new filter to the sidebar search ('Devices without linked asset').

* CORE: Added possibility to bulk-edit 'name', 'venture', 'role' and 'physical parent device'.

* CORE: Improved 'DNS Records' form validation (detection of duplicate records).

* CORE: Some small improvements related to integration with 'ralph_assets' and 'ralph_pricing' (e.g. a script for uploading data re: venture/IPs ownership).

* CORE: Added 'notifications' module (a simple app for sending and archiving e-mails when you want to be notified of certain events, e.g device's configuration change).

* SCAN: Fix for 'ssh_xen' plugin (reference to a non-existing variable).

* CORE: Added 'DeviceEnvironment' model along with adding 'service' and 'device_environment' fields on 'Device' model (needed for future features).

* CORE: Added 'venture' field to the 'IPAddress' resource in API.

* SCAN: Minor fixes for 'ssh_cisco_catalyst' and 'ssh_cisco_asa' plugins (e.g. NotConfiguredError could break all Scan processes).

* SCAN: 'management' field on 'Device' model is no longer ignored ('ssh_proxmox' plugin mostly).

* CORE: Fix for syncs with LDAP.

* SCAN: Fix for sysinfo extraction in 'ssh_3par' plugin.

* DonPedro: added normalization of WWNs and some additional command-line options for the output generation.

* SCAN: Enabled saving of the results in 'mount_shares' postprocessing plugin.

* CORE: Added missing permissions checks to the views.

2.0.0-stable
~~~~~~~~~~~~

Released on July 9, 2014

This is a stable release.

* SCAN: Disk shares detection - disk shares without physical volume in OS are now detected, better merging of results.

* SCAN: ssh_proxmox changes - root user is now not required.

* SCAN: SNMP - AES priv protocol support.

* SCAN: SSH AIX - added normalization for wwns from aix plugin.

* SCAN: Scan postprocess is not disabled by default.

* SCAN: MAC addresses normalization.

* SCAN: [vmware plugin] subdevices w/o MAC addresses shouldn't be included in scan results.

* SCAN: Fixed 3par plugin #892 return results instead device_info.

* SCAN: Fixed ascii encoding problem in ssh_xen plugin.

* SCAN: Onstor now collects diskshare mounts.

* SCAN: Fixed getting info from multipath when there are multipath config warnings.

* Feature/pricing api - shares - venture and virtual filters - pricing api: shares changed (back) to share mounts; added venture param and virtual mounts filter

* CMDB: New semantics - used uid instead of id for JIRA.

* CMDB: Inactive CI's are not displayed by default, use checkbox to include them optionally.

* CMDB: Changes importing are now handled by searching by creation date.

* CMDB: Collecting events that can possibly affect a CI (events on children).

* DHCP: Fix protect against IP addresses with the same domain tests.

* CORE: Pluggable apps permissions and ralph_permission decorator. Improved permissions to pluggable apps; ralph_permission decorator could now be applied to dispatch method (before only to post/get/etc methods);

* CORE: Fixed sorting by network address/gateway in admin (incl. migration).
  Network model gets new field gateway_as_int, which is used for sorting by "Gateway address" column ("Network address" column now uses min_ip field for this).

* CORE: Implemented 3 bound permissions per Ralph application (has_core_access, has_asset_access, has_scrooge_access).

* CORE: Disk shares in admin are now loading faster.

* CORE: Added getting device by ip address or remark to the pricing api.

* CORE: Fixed sorting by network address/gateway in admin (incl. migration).

* CORE: Pillow upgraded to 2.2.0.

* CORE: Added FC cards to the pricing API.

* CORE: Readonly widget has better appeareance.

* CORE: Added Docker installation method.

* DonPedro: Better FC and share mounts detection.

* DonPedro: Additional logging and mac addresses normalization.

2.0.0-rc8
~~~~~~~~~

Released on June 3, 2014

This is a final bugfix RC Release with new features. It brings Quickscan feature and better API compatibility, as well as many scan, networks and ui stability improvements.

* SCAN: Added "Quick scan" features which is the quickest way to scan given ip address.

* SCAN: Now scan post processings plugins are running from main scan job.

* SCAN: [hp_oa plugin] added 'Apache' to known HTTP family names.

* SCAN: Manual prescan (autoscan) shouldn't be run as a separate job.

* SCAN: Fix for UnicodeEncodeError. Sometimes plugins can return non ASCII characters...

* SCAN: Timeout of rq_jobs is now configurable.

* SCAN: Fix for Proxmox3 (family recognizing + listening port).

* SCAN: ssh_ibm_bladecenter fixed better choices finding (for components or device types).

* SCAN: Added autoscan (prescan) at the beginning of the manual scan.

* SCAN: Added Quickstan feature for quickly scanning given IP Address.

* SCAN: [vmware plugin] subdevices w/o MAC addresses shouldn't be included in scan results.

* SCAN: 3par plugin now works correctly - return results instead device_info.

* CMDB: Events are now bound many-to-many to CIs.

* CMDB: Inactive CIs are not displayed by default.

* CMDB: Unified the search of CIs in CMDB.

* CMDB: Corrected icon class for venturerole.

* CMDB: New ralph-independent way of setting icons for CIs.

* CMDB: provided correcting ownership duplicates.

* CMDB: Event is propagated from parent CI to its children.

* API: fixed api for pricing.

* API: State is no longer copied in Service API.

* CORE: Fix test-with-coveralls make command - convert spaces to tab. Ommit test files in coverage.

* CORE: Update Travis badge.

* CORE: Override for a django bug with "View on site".

* CORE: Improved mapping ad groups -> django groups.

* CORE: Fixed 'Bulk edit' button on 'Ventures' and 'Racks' views.

* CORE: Networks - Fixed Handling networks with gereric IDs instead of names.

* NETWORKS: Networks performance improved - extended caching timeout.

2.0.0-rc7
~~~~~~~~~

Released on May 15, 2014

This is a 7th Release Candidate release with bugfixes only.

* CORE: Fixed 'Bulk edit' button on 'Ventures' and 'Racks' views.

* CORE: Handling networks using IDs instead of their names.

* CORE: Fixed and improved/cleaned 'Bulk edit' form.

* CORE: Got rid of 'Model Group' and 'Model' columns in 'Software' tab.

* CMDB: Additional CIs for CMDB events.

* CMDB: sAMAccuntName can be synchronised from AD for CIOwners.

* SCAN: Whole new SCAN documentation prepared.

2.0.0-rc6
~~~~~~~~~

Released on April 28, 2014

This is a 6th Release Candidate release with more testing.

* SCAN: Stability improvements and fixes.


2.0.0-rc5
~~~~~~~~~

Released on May 15, 2014

This is a 5th Release Candidate release.

* many fixes

2.0.0-rc4
~~~~~~~~~

Released on May 15, 2014

This is a 4th Release Candidate release.

* Scan - special queues for UI calls

* many fixes

2.0.0-rc3
~~~~~~~~~

Released on May 15, 2014

New features:

* CORE: added `logical parent` for stacked devices, when physical parent is not enough.

* DHCP: configuration file for DHCP can be generated for multiple environments or data centers at once.

Optimizations:

* NETWORKS: performance improvements: reduced unresponsive rendering of networks tree to ~ 1 sec

* SCAN: performance improvements: reduced time of traversing through large number of intersecting networks

* CORE: many cmdb, scan, deployment fixes.

2.0.0-rc2
~~~~~~~~~

Released on May 15, 2014

New features:

* SCAN: Much more advanced Scan module with great performance and *real* plugins architecture with JSON API.

* SCAN: New vmware plugin for discovering virtual machines.

* SCAN: Cisco Catalyst and Juniper switches detection with recognizing stacked subswitches added.

* NETWORKS: Completely new Network panel which allows you to manage IP addresses and netmasks easily.

* DNS: Added additional validation for DNS form (one PTR is required now).

* DHCP: Added additional validation for DHCP form.

* Environments - place where you can configure discovery queue or hosts naming temeplate.

* LDAP group mapping allows you to more specific permissions setting directly via LDAP.

Optimizations:

* DHCP config - fixes for networks and entries.

* DHCP config - large (10x) speed improvements while generating configs.

* Updated ralph_dhcp_agent.

* New white theme.

* Ralph CLI integrated into the UI.

Core changes:

* CORE: Reworked Dependency Injection of Ralph submodules thanks to DjangoPluggableApp, giving more power and DRY-ness.

* SCAN: Upgraded detection of newer Dell machines using IDRAC protocol.

* SCAN: Fixed xen hypervisor discovery, where virtuals were incorrectly assigned to the master cluster.

* Fixed bug where gateway was always required.

* CMDB: Fixed compatibility with Zabbix where zabbix_id was out of range (#726)

* CMDB: Fixed filtering Incidents/Problems using start date, end date.

* CMDB: API: Added impact links to the CI's.

* CMDB: Improved CMDB API documentation.

* CMDB: Fixed Jira<->CMDB integration where only first 1000 issues were imported.

* CMDB: Fixed CMDB bugs where customfields where not visible correctly on particular CITypes.

* CMDB: Allowed CMDB to register own CITypes via Admin Panel.

2.0.0-rc1
~~~~~~~~~

Released on May 15, 2014

This is release with new features.

* Added completely new Scan module - new DC discovery mechanism which allows you to better maintain periodic scans, and much easier to write new discovery plugins using JSON API.

* Custom fields defaults (from venture_role) now appears correctly in the API.

* Added API for Scan module.

* CMDB Api documentation refactored.

* Tastypie API fixed.

1.2.9
~~~~~
Released on November 06, 2013

This is semi-final :) hotfix release.

* Fixed API problem.

* Fixed incompatible inquiry problem.

1.2.8
~~~~~
Released on November 04, 2013

This is hotfix release - fixes broken dependency.

* Fixed django-bob dependecy.

1.2.7
~~~~~
Released on October 31, 2013

This is as bugfix release.

* Added new search field in device - Deprecation (based on Device.deprecation_kind)

* Added Asset tab for views with informations about devices

* Added info on form validation errors (wishlist 15); added terabytes as unit
  in size_divisor.

* ``Venture`` dropdown on ``Info`` now displays items in proper hierarchy.

* Fixed links to Jira tickets in CMDB's Jira Changes, Problems and Incidents.

* Venture's deletion in admin is now disabled; name/symbol cannot be changed once verified (schema migration on ``Venture`` model).

* Fixed ``http`` plugin -  recognition Cisco ASDM 7.1

* Improved asynchronous report logic

* New column in assets - is discovered

* New search field in devices - deprecation kind

* New search field in assets - deprecation rate

* Some changes in load balancer addresses view

1.2.6
~~~~~
Released on August 08, 2013

This is as bugfix release.

* Fixed plugin ``ssh_cisco_asa`` - plugin not responding,

* Added new resources to API: Network, NetworkKind.

* Added ``network_details`` to Ipaddress API resource.

* Extra costs that don't appear in the given time range are not displayed in the venture summery view.

* ``Numeric position`` field no longer required.

* ``Barcode`` field (in admin) can be set to None for more than one devices.

* Fixed owners links in admin/business/ventures; fixed admin history change.

1.2.5
~~~~~
Released on July 17, 2013

This is a minor bugfix release. Bugfixes in the discovery module and
documentation enhancements.

* Added documentation for the discovery subsystem.

* Added new Xeon processors support.

* Added data_center and rack to the puppet classifier output.

* Fixed DonPedro 'ipaddress' KeyError.

* Disabled reboot plugin for the deployment.

* Fixed XEN disk discovery.

* Added property_types to the puppet classifier response.

* Ralph search results are now unique.

* Fixed border-case for lshw discovery when response tag is none.

* Fixed OpenStack plugin - assigning costs to the wrong device

1.2.4
~~~~~
Released on June 18, 2013

This is a bugfix release.

* Bugfixes in discovery module.

* Extended APIs for assets and pricing.

1.2.3
~~~~~

Released on June 7, 2013

This is a bugfix release.

* Enhancements to the Ventures - added Profit Center and Business Segment information.

* Added ability to import Ventures data(PC, Business Segment) from CSV file.

* Added API integration with Ralph Pricing and Ralph Assets.

* Fixed puppet classifier crashing on models without model group.

* Fixed 3PAR detection.

* Better error reporting for discovery errors.

* PostgresSQL support provided.

* Fixed hostname validation in the deployment area.

* Testing profiles updated.

* Fixed out of range error while discovering devices with unknown Networks.

1.2.2
~~~~~

Released on April 23, 2013

This is a bugfix release.

* Removed Git, hostname and stty process forking.

* Cleaned up plugins chains.

* Fixed pagination, templates and filters in the CMDB.

1.2.1
~~~~~

Released on April 16, 2013

This is a bugfix release.

* Fixed bug in the Catalog and Account areas.

* API permissions fixed.

1.2.0
~~~~~

Released on April 15, 2013

This is a major release. It brings new big features and bugfixes.
Added new modules: asset management, ralph beast command line client, windows software discovery.
Replaced workers architecture with RQ.
New integrations with external systems. And much more.

* Replaced Celery asynchronous worker engine with RQ, see:
  http://python-rq.org.

* Introduced Ralph commandline tool - Beast, see:
  https://github.com/allegro/ralph_beast.

* Introduced Offline Asset Mgmt module for Ralph, see:
  https://github.com/allegro/ralph_assets.

* Discovery improvements: added Ganeti devices support, Juniper and Nortel
  switches, 3ware controllers. Added new Puppet REST integration.

* Introduced discovery for Windows Sofware via Don-Pedro plugin and extended
  ability to search software versions using complex operators (<, <=, >, >= etc).

* CMDB-Splunk integration introduced.

* Reports are now asynchronous (don't block the UI anymore, happen on the queue).

* Added User Preferences framework - for now with the ability to change landing
  page per user.

* REST API extended - new filters and new resources (owners).

* Deployment improvements: statuses plugin fixed, duplicating networks added,
  ``firstfreeip`` function fixed.

* Performance improvements in the CMDB.

* Many Ralph UI bugs and discovery fixes.

1.1.18
~~~~~~

Released on March 19, 2013

This is a major release. It brings new big features and bugfixes.
Introduced 3rd party module for Ralph - Offline Assets Management
Added CMDB - Splunk integration.
Added archivization feature for CMDB.
Added AutoCI feature for CMDB.
Improved Jira integration.
Added ability to discover Windows software using don pedro plugin.
Discovery of hardware fixed and improved.

* Added CMDB - Splunk integration.

* Added archivization feature for CMDB.

* Added Autoci feature for CMDB.

* Improved jira integration.

* Added ability to discover Windows software using don pedro plugin.

* Discovery of hardware fixed and improved.

1.1.17
~~~~~~

Released on February 19, 2013

This is a bugfix release.

* Editable layers in CMDB.

* Bugfixes in discovery plugins and CMDB.

* Performance improvements in CMDB report.


1.1.16
~~~~~~

Released on February 07, 2013

This is a major release with new features.

* Adding next-server to DHCP configuration for devices in deployment.

* A new report for device costs.

* Improved CMDB impact report.

* The ability to import DNS records from a CSV file.

* Show separate count for physical devices in ventures report.

* More bugfixes in the discovery plugins.

1.1.15
~~~~~~

Released on January 16, 2013

This is a major release with new features.

* Added custom DHCP configuration for networks and DHCP servers.

* Networks can now be marked as non-unique, which prevents their IP addresses
  from being added to devices.

* Next free hostname and IP address are now displayed in the Addresses tab.

* Bugfixes in discovery plugins.

1.1.14
~~~~~~

Released on January 07, 2013

This is a bugfix release.

* Add detailed costs to the Ventures report,

* Fix incorrect use of concurrent_get_or_create in discovery plugins

* Fix the clean deployment plugin to re-connect the ip address

1.1.13
~~~~~~

Released on December 31, 2012

This is a bugfix release.

* Allow bulk deployment to re-use existing devices

* Clean up the way in which the discovery plugins create components

* Allow racks in different data centers to have the same name

1.1.12
~~~~~~

Released on December 20, 2012.

This is a bugfix release.

* Dell PowerEdge servers supported

* introduced pricing groups for disk shares

* interpolation of variables in preboot files supported

* simplified deployment workflow (no issue tracked based acceptance involved)

* mass deployment

* discovery fixes

1.1.11
~~~~~~

Released on December 5, 2012.

This is a bugfix release.

* Fix bugs in the search and add device forms

1.1.10
~~~~~~

Released on December 5, 2012.

This is a bugfix release as well as new discovery and usability features.

* support for SNMPv3 in discovery

* DHCP config improvements: proper hostnames from PTR records; support for
  syncing entries and networks from a specific DC only

* DNS/DHCP addresses tab redesigned for usability and performance

* improved search for software components and discovering software versions

* discovery fixes

1.1.9
~~~~~

Released on November 26, 2012.

This is a bugfix release. Fixes regressions in discovery from version 1.1.9 and
introduces DiscoveryWarnings for tracking problems with discovery.

* Fixes for discovery regressions from 1.1.8

* DiscoveryWarnings introduced

1.1.8
~~~~~

Released on November 22, 2012.

This is a major release.
Includes system-level storage detection, improved CPU information for Windows
machines, ability to edit DNS information straight from the Addresses tab on a
device. CMDB now includes an impact report.

* system-level storage detection stored in the OperatingSystem component

* improved CPU information in DonPedro Windows agent

* CPU information is stored in history for financial reports

* DNS entries can be edited on the Addresses tab for every device

* CMDB: impact report introduced, API for CI changes, layers and types

* Installed software packages reported by Puppet are stored in the inventory
  database

* Base64 support for compressed Puppet fact values

* Minor bugfixes

1.1.7
~~~~~

Released on November 8, 2012.

This is a bugfix release. Includes fixes in IPMI, SSG and Xen discovery as well
as minor CMDB and DNS admin improvements. DHCP agent script is now compatible
with Python 2.4 (for usage in RedHat 5.x environments).

* Stability improved for discovering SSG firewalls

* ``ralph_dhcp_agent.py`` is now compatible with Python 2.4

* Uses the forked ``django-powerdns-dnssec`` package for improved PowerDNS
  support

* Xen discovery support fixed (memory was reported in wrong units)

* IPMI discovery improved for Sun and Supermicro servers

* Minor CMDB improvements

* Minor bugfixes

1.1.6
~~~~~

Released on October 29, 2012.

This is a bugfix release. Includes fixes in CMDB, device admin, device report
and unit tests.

* CMDB fixes: owners not required when saving a CI, cycles in relationships are
  detected, only manual changes generate tickets in external trackers

* fixed `issue #183 <https://github.com/allegro/ralph/issues/183>`_: "Unknown"
  rack unsupported

* device admin fixes: model validatation, saving uses priorities

* ``paramiko`` library used for SSH connectivity instead of the ``ssh`` fork

* minor device report fixes

* unit tests improved

1.1.5
~~~~~

Released on October 19, 2012.

This is a bugfix release. Fixes order of database migrations and several
problems with running unit tests. Django version bumped to 1.4.2.

* bumped Django version to 1.4.2

* fixes order of database migrations

* fixes a problem in Django 1.4.x with built-in unit tests failing because of
  settings used

* minor CMDB fixes

* more unit tests

1.1.4
~~~~~

Released on October 15, 2012.

This is a minor release. Adds role properties to the RESTful API.
Fixes deprecation so that deprecated devices no longer report a monthly cost.

* role properties available in API

* virtual CPU count in the main ventures report

* deprecated devices now have a zero monthly cost

1.1.3
~~~~~

Released on October 10, 2012.

This is a bugfix release. Contains fixes in UI and discovery code, as well as
shows cloud usage in the main venture report.

* cloud usage is visible in the main ventures report

* several minor fixes in UI and new plugins

1.1.2
~~~~~

Released on October 8, 2012.

This is a bugfix release. Includes a new experimental discovery agent for
Windows called Donpedro as well as two new discovery plugins for Xen
hypervisors and Linux machines not controlled by Puppet. Fixes bugs in UI, CMDB
and discovery.

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

This is a bugfix release. Includes fixes in discovery and UI code, as well as
updates in the price catalog: history of changes is tracked and the UI for
specifying price per unit of size is now easier to use.

* Price catalog updated: history of changes tracked, a more intuitive UI for
  prices per unit of size

* bug fixes in discovery and UI

1.1.0
~~~~~

Released on September 19, 2012.

This is a feature release. Includes support for deployment of physical hosts
using PXE, simplified financial model (components can be now priced by unit of
size, e.g. by core or GiB) and upgraded reporting system. Includes minor bug
fixes.

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

This is a bugfix release. Includes fixes in CMDB and UI code, as well as a
preliminary timeline view for CMDB, usability improvements in editing CI
relations.

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

This is a bugfix release. Includes fixes in CMDB, discovery and UI code, as
well as the possibility to specify extra queries for OpenStack. Local storage
costs are now also counted for Proxmox virtual machines.

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

This version has report and rack views, as well as some improvements in the
user interface and important bug fixes in the discovery plugins. You can now
delete from the database old devices that are no longer needed.

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

This is a bugfix release. Includes fixes for minor issues in the Web app and
ability to run CMDB integration plugins remotely. It introduces a rudimentary
reports tab on device lists.

* a rudimentary reports tab on device lists to filter devices according to
  specified rules

* venture tree collapsible

* CMDB integration scripts integrated into framework

* CMDB supports distributed plugins

* minor fixes in the Web app

1.0.2
~~~~~

Released on July 23, 2012.

This is a bugfix release. It introduces the ability to create new devices
manually (without autodiscovery) and fixes several minor issues.

* ``ralph chains`` command to list available plug-in chains

* fixed regression from 1.0.1: ``settings-local.py`` works correctly again

* ability to create new devices from the web application

* several minor bugfixes

* added cmdb charts for dashboard

1.0.1
~~~~~

Released on July 18, 2012.

This is a bugfix release. It fixes several small problems with initial setup
and configuration, and makes it easier to manage settings.

* ``ralph`` management command introduced as a shortcut to ``python manage.py``

* ``ralph makeconf`` management command introduced to create configuration from
  a template

* PyPI package fixed by including all resources in the source package

* minor fixes for the SQLite backend

* minor documentation fixes and updates

1.0.0
~~~~~

Released on July 16, 2012.

This is the first release of Ralph.

* initial release
