.. _cmdb:

Overview
========

Ralph provides an early (experimental) version of a Configuration Management
Database module.

CMDB module
-----------

Ralph's CMDB module is an ITIL-related functionality.  It enables you to
manage infrastructure, and other components relations. It also lets you connect
CIs with events, tasks and tickets that are assigned to them. With this module
you can:

1) focus not only on infrastructure but also on business processes,
2) use layers and relations to bundle related components,
3) integrate with external systems: monitoring, deployment, version management
   repository, ticketing tool, and others, keeping references between CIs and
   events.

Goals and Use Cases
-------------------

CMDB's main goals are to:

1) support ITIL-related processes with information on service architecture and
configuration,
2) enable analysis of impact of failures and changes, based on CI relations,
3) enable analysis of maintainability of CIs by matching events to specific CI.

CMDB is designed for:

* Process Managers and Line Managers -- to audit architecture and relate CIs
  to specific actions taken by system administrators and developers;
* System administrators -- to assess impact of their work or observed failures;
* Decision makers -- to assess costs of maintenance per CI and refer it to
  actual costs, P&Ls related to offered service.

For example:

1) There is a change planned to roll out new OS version on number of hosts --
based on the CMDB relations it is possible to assess, regardless of whether
the environment is virtual or physical:

* scope of the change -- how many hosts are affected,
* impact of the change -- which services are potentially affected and whether
  the change will require downtime or will result in failure,
* potential coworkers -- people to inform (based on Technical/Business
  Owner information) who need to monitor, trace and relate (if applicable)
  the events observed during deployment.

2) When there is a group of 50 hosts used for similar purposes and one of them
is faulty without a known reason:

* CMDB will enable assessment of impact of the failure,
* it will list a number of events and relate one to another,
* based on the above and the financial information (costs of maintenance,
  costs of system administrator work, costs of unavailability) it will
  support decisions about planning changes.



System architecture overview
----------------------------

CMDB (Configuration Management DataBase) maintains a complete Assets
information for the Change Management Process. In order to do it, it
tracks all events and changes in all the IT Systems used in production.

The CMDB specification requires that the data is kept in canonical form of CI's
(Configuration Items) and relations between them.  The CMDB data structure is
organized into this form to give possibility of reporting the relations and
dependencies between IT components.  That makes it easy to calculate overall
impact of a single change.

Right now CMDB module provides following features:

* ability to create relations between CI's: contains, is part of, requires, is
  required by, is role for, has roles;
* ability to assign layers to CI's;
* statistics of changes and reporting of most changed/inactive CI's;
* adding custom attributes to CI's, depeding on its type;
* ability to extend by custom layers, relations, and types.

The CMDB module federates and reconciles data from number of systems to get the
big picture of your IT Infrastructure Changes.

In Ralph CMDB we consume following services:

1) infrastructure monitoring systems like Zabbix,
2) service configuration systems like Puppet,

- versioning configuration,
- agent reconfiguration notifications,

3) asset management software -- Ralph,
4) issue tracker -- Jira recorded incident/problem tickets.

and others.

Installation
------------

The CMDB module is included in Ralph right out of the box.  Make sure the
``cmdb`` app is activated in your :ref:`configuration <configuration>` by
checking if ``cmdb`` is listed in ``INSTALLED_APPS``::

    INSTALLED_APPS=[
    'ralph.cmdb',
    ...
    ...
    ]

.. note::

    Currently the CMDB module requires MySQL database as backend. We accept
    patches.

Layers customization
~~~~~~~~~~~~~~~~~~~~

All CIs can be grouped in layers. By default ``cmdb`` have predefined
set of layers:

1) Applications
2) Databases
3) Documentation/Procedures
4) Organization Unit/Support Group
5) Hardware
6) Network
7) Services
8) Roles

All layers can be customized in admin panel. Administrator can modify:
* name - name of the layer
* connected types - set of connected CIType objects.By these relationships ``cmdb`` 
can assign CI to the appropriate layer.
* icon

Adding new layers is also possible.

Federating the data
-------------------

The federated database needs to be populated from third party services.
However, CMDB is not a real-time database. Instead, assets and integration data
must be imported at some interval in order to show up in CMDB.

Two different commandline scripts are used to populate CMDB database --
``ralph cmdb_sync`` and ``ralph cmdb_integration``.

* To populate database with assets coming from Ralph CMDB, use ``cmdb_sync``.
* To fill database with third party services data, use ``cmdb_integration``.


cmdb_sync
~~~~~~~~~

This command line utility is used to create CI/Relations/Layers data from Ralph
Assets Management Database.  Every Device, Network, Venture, etc. must have its
own counterpart in the CMDB database.  To keep assets in sync with Ralph core
you should run ``ralph cmdb_sync`` at some interval, e.g. once per day.  If you need
more accurate data, set up a cron job for more frequent invocations.

Populating the CMDB database with assets::

    $ ralph cmdb_sync --action=import --kind=ci

Populating the CMDB database with asset relations::

    $ ralph cmdb_sync --action=import --kind=all-relations

For help use ``--help``::

   Usage: cmdb_sync --action=[purge|import]
   --kind=[ci/user-relations/all-relations/system-relations] --content-types

   Options:
   -h, --help            show this help message and exit
   --action=ACTION       Purge all CI and Relations.
   --kind=KIND           Choose import kind.
   --ids=IDS             Choose ids to import.
   --content-types=CONTENT_TYPES
                         Type of content to reimport.

cmdb_integration
~~~~~~~~~~~~~~~~

Federating data from third party services (choose one or all)::

    $ ralph cmdb_integration --cmdb_git --cmdb_jira --cmdb_zabbix

Options:
  -v VERBOSITY, --verbosity=VERBOSITY
                        Verbosity level; 0=minimal output, 1=normal output,
                        2=verbose output, 3=very verbose output
  --settings=SETTINGS   The Python path to a settings module, e.g.
                        "myproject.settings.main". If this isn't provided, the
                        DJANGO_SETTINGS_MODULE environment variable will be
                        used.
  --pythonpath=PYTHONPATH
                        A directory to add to the Python path, e.g.
                        "/home/djangoprojects/myproject".
  --traceback           Print traceback on exception
  --cmdb_zabbix         Trigger cmdb_zabbix plugin
  --cmdb_git            Trigger cmdb_git plugin
  --cmdb_assets         Trigger cmdb_assets plugin
  --cmdb_jira           Trigger cmdb_jira plugin
  --remote              Runs on remote worker
  -d DAYS, --days=DAYS  Number of days from now back to be checked
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  

Zabbix integration
------------------
Events triggered from Zabbix give us information about, for example:

- processor usage is to high,
- free RAM is too low,
- disk usage is too low.

We collect this data using Zabbix Integration API v 2.0.
It simply uses REST services for retrieving:

- hosts id from Zabbix,
- trigger information.

Information from Zabbix shows up on the CI preview screen in the 'Monitoring
events' section.

CMDB database of hosts have to be populated with host name(ci name = hostname) in order to connect the triggers to them.

.. note::
  If you want, the zabbix plugin can register missing CI's hostnames while importing the data. You have to set the ZABBIX_IMPORT_HOSTS to True in this case. By default, no zabbix hosts are registered in the CMDB database while importing(ZABBIX_IMPORT_HOSTS=False).


Setup
~~~~~
Add to settings::

    ZABBIX_USER="..."
    ZABBIX_PASSWORD="..."
    ZABBIX_URL="..."
    ZABBIX_IMPORT_HOSTS=False

and run::

    $ ralph cmdb_integration --zabbix_hosts --zabbix_triggers

to create Zabbix relations and download trigger data.


Puppet Agents integration
-------------------------

The Puppet agent sends report in YAML format after every reconfiguration.  That
report describes what has changed after host reconfiguration.  In order to use
this mechanism, you should change configuration of Puppet Master to point
the puppet reports URL to the CMDB URL::

    #
    #  /etc/puppet/puppet.conf
    #

    [agent]
        report = true
        reporturl = http://your_cmdb_url/cmdb/rest/notify_puppet_agent

Every puppet report is saved into the database. You can see it from CI View tab
called 'Agent events'.

If you use Puppet Dashboard and have already specified ``reporturl``, there is
a trick to allow multiple URLs to be given.  Since Puppet doesn't support
specifying multiple URLs at the moment, you can use this example report script::

    $ cat /usr/lib/ruby/1.8/puppet/reports/cmdb.rb

    require 'puppet'
    require 'net/http'
    require 'uri'

    Puppet::Reports.register_report(:cmdb) do

      desc <<-DESC
      CMDB Report example
      DESC

      def process
        url = URI.parse("(your_ralph_url)/cmdb/rest/notify_puppet_agent/")
        req = Net::HTTP::Post.new(url.path)
        req.body = self.to_yaml
        req.content_type = "application/x-yaml"
        Net::HTTP.new(url.host, url.port).start {|http|
          http.request(req)
        }
      end
    end


Jira Integration
----------------

You can show Jira issues relating to the given CI by using Jira integration
mechanism.

Setup
~~~~~
Set options::

    JIRA_USER="jira_user"
    JIRA_PASSWORD="jira_pass"
    JIRA_URL="http://jiraurl" # main url, without trailing slashes
    JIRA_CI_CUSTOM_FIELD_NAME="customfield_number"

where ``JIRA_CI_CUSTOM_FIELD_NAME`` is name of custom ``ci`` field added to
Jira, which contains CI UID key.

Then run (or add a cron job)::

    $ ralph cmdb_integration --jira

to download all Problems/Incidents from remote Jira server into the CMDB
database.


Fisheye Integration
-------------------

You can track changes in Puppet configurations stored in Fisheye/GIT/SVN/
repository by running::

    $ ralph cmdb_integration --git


Splunk
------

If you configure ``SPLUNK_LOGGER_PORT`` and ``SPLUNK_LOGGER_HOST``, then
information about CIChangeGit, CIChangePuppet will be sent to Splunk.
In Splunk you must configure new **Data Input with TCP port** in Splunk.
For more information about configure Splunk go to


API
----

More information about accessing to the CMDB can be found in :ref:`cmdb_resources`


Future Releases
---------------

There are following features planned for future releases:

1) autodection of Applications and Databases used on hosts,
2) reports/dashboards for Management use,
3) visualization of CMDB data,
4) integration with more systems, including security testing.

