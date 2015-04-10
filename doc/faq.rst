.. _faq:

==========================
Frequently Asked Questions
==========================

Integration
-----------

How can I set up LDAP authentication?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You will need to install ``django-auth-ldap`` and ``python-ldap`` using
``pip``. Then add LDAP as an authentication backend in your local settings::

  AUTHENTICATION_BACKENDS = (
      'django_auth_ldap.backend.LDAPBackend',
      'django.contrib.auth.backends.ModelBackend',
  )
  LOGGING['loggers']['django_auth_ldap'] = {
      'handlers': ['file'],
      'propagate': True,
      'level': 'DEBUG',
  }

You will need to configure the LDAP connection as well as mapping remote users
and groups to local ones. For details consult `the official django-auth-ldap
documentation <http://packages.python.org/django-auth-ldap/>`_. 
For example, connecting to an Active Directory service might look like this::

  import ldap
  from django_auth_ldap.config import LDAPSearch, GroupOfNamesType
  AUTH_LDAP_SERVER_URI = "ldap://activedirectory.domain:389"
  AUTH_LDAP_BIND_DN = "secret"
  AUTH_LDAP_BIND_PASSWORD = "secret"
  AUTH_LDAP_PROTOCOL_VERSION = 3
  AUTH_LDAP_USER_USERNAME_ATTR = "sAMAccountName"
  AUTH_LDAP_USER_SEARCH_BASE = "DC=allegrogroup,DC=internal"
  AUTH_LDAP_USER_SEARCH_FILTER = '(&(objectClass=*)({0}=%(user)s))'.format(
    AUTH_LDAP_USER_USERNAME_ATTR)
  AUTH_LDAP_USER_SEARCH = LDAPSearch(AUTH_LDAP_USER_SEARCH_BASE,
    ldap.SCOPE_SUBTREE, AUTH_LDAP_USER_SEARCH_FILTER)
  AUTH_LDAP_USER_ATTR_MAP = {"first_name": "givenName", "last_name": "sn",
      "email": "mail"}
  AUTH_LDAP_PROFILE_ATTR_MAP = {
      "company": "company",
      "manager": "manager",
      "department": "department",
      "employee_id": "employeeID",
      "location": "officeName",
      "country": "ISO-country-code",
  }

However, when using OpenDJ as a LDAP server, ``AUTH_LDAP_USER_USERNAME_ATTR`` should be equal to ``uid``::

  AUTH_LDAP_USER_USERNAME_ATTR = "uid"

For other implementations objectClass may have the following values:

 * Active Directory: objectClass=user,
 * Novell eDirectory: objectClass=inetOrgPerson,
 * Open LDAP: objectClass=posixAccount

Manager is special field and is treated as reference to another user,
for example "CN=John Smith,OU=TOR,OU=Corp-Users,DC=mydomain,DC=internal"
is mapped to "John Smith" text.

Country is special field, the value of this field must be a country code in the
`ISO 3166-1 alfa-2 <https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2>`_ format.

Ralph provides ldap groups to django groups mapping. All what you need to
do are:

 * import custom ``MappedGroupOfNamesType``,
 * set up group mirroring,
 * declare mapping.

::

  from ralph.account.ldap import MappedGroupOfNamesType
  AUTH_LDAP_GROUP_MAPPING = {
    'CN=_gr_ralph,OU=Other,DC=mygroups,DC=domain': "active",
    'CN=_gr_ralph_assets_buyer,OU=Other,DC=mygroups,DC=domain': "assets-buyer",
    'CN=_gr_ralph_assets_helper,OU=Other,DC=mygroups,DC=domain': "assets-helper",
    'CN=_gr_ralph_assets_staff,OU=Other,DC=mygroups,DC=domain': "assets-staff",
    'CN=_gr_ralph_admin,OU=Other,DC=mygroups,DC=domain': "superuser",
    'CN=_gr_ralph_staff,OU=Other,DC=mygroups,DC=domain': "staff",
  }
  AUTH_LDAP_MIRROR_GROUPS = True
  AUTH_LDAP_GROUP_TYPE = MappedGroupOfNamesType(name_attr="cn")
  AUTH_LDAP_GROUP_SEARCH = LDAPSearch("DC=organization,DC=internal",
      ldap.SCOPE_SUBTREE, '(objectClass=group)')

Note: For OpenDJ implementation ``AUTH_LDAP_GROUP_MAPPING`` is not obligatory. ``AUTH_LDAP_GROUP_TYPE`` and ``AUTH_LDAP_GROUP_SEARCH`` should be set as follows::

  from django_auth_ldap.config import GroupOfUniqueNamesType
  AUTH_LDAP_GROUP_TYPE = GroupOfUniqueNamesType()
  AUTH_LDAP_GROUP_SEARCH = LDAPSearch("DC=organization,DC=internal",
    ldap.SCOPE_SUBTREE, '(structuralObjectClass=groupOfUniqueNames)')


If you want to define ldap groups with names identical to ralph roles, you
shouldn't declare mapping ``AUTH_LDAP_GROUP_MAPPING``. If there are any one
mapping defined another groups will be filtered. Some groups have
special meanings. For example users need to be in ``active`` to log in,
``superuser`` gives superuser privileges. You can read more info
in :ref:`groups`.

You can define users filter, if you don't want to import all users to ralph::

    AUTH_LDAP_USER_FILTER = '(|(memberOf=CN=_gr_ralph_group1,OU=something,'\
        'DC=mygroup,DC=domain)(memberOf=CN=_gr_ralph_group2,OU=something else,'\
        'DC=mygroups,DC=domain))'

In case of OpenDJ please use ``isMemberOf`` instead of ``memberOf``.

    
Gunicorn
--------

Can I start Gunicorn using the traditional start-stop-daemon?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Sure, here is the ``init.d`` recipe for Debian/Ubuntu: `/etc/init.d/gunicorn
<_static/gunicorn>`_. Just alter the ``CONFDIR`` and ``VENV_ACTIVATE``
variables. Note: ``service gunicorn restart`` only HUPs the server. If an actual
restart is necessary, use the ``service gunicorn force-restart`` command.

If you happen to have a script like this for another operating system, contact
us so to include it here.

MySQL
-----

The web app shows error screens with database warnings about incorrect characters.
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

On many systems the default configuration of MySQL is not optimal. Make sure
that your tables are using UTF-8 as the character set, with compatible collation
and InnoDB storage engine. Example::

  mysql> alter table TABLENAME engine=innodb;
  mysql> alter table TABLENAME convert to character set utf8 collate utf8_general_ci;

My worker creates a new database connection on each task.
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This is `a known limitation of Django
<https://code.djangoproject.com/ticket/11798>`_. The best solution is to set up
a ``mysql-proxy`` instance which will reuse actual database connections and set
up Ralph to use that. First install ``mysql-proxy``::

  $ sudo apt-get install mysql-proxy

Then edit ``/etc/default/mysql-proxy`` so it says::

  ENABLED="true"
  OPTIONS="--proxy-backend-addresses=mysqlserverhost.local:3306 --log-level=info --log-use-syslog --proxy-address=127.0.0.1:4041 --admin-username=ralph --admin-password=ralph --admin-lua-script=/usr/lib/mysql-proxy/lua/admin.lua"

Start the proxy::

  $ sudo service mysql-proxy start

In ``/var/log/syslog`` you should see::

  Jul 25 10:44:14 s10337 mysql-proxy: 2012-07-25 10:44:14: (message) mysql-proxy 0.8.1 started
  Jul 25 10:44:14 s10337 mysql-proxy: 2012-07-25 10:44:14: (message) proxy listening on port 127.0.0.1:4041
  Jul 25 10:44:14 s10337 mysql-proxy: 2012-07-25 10:44:14: (message) added read/write backend: mysqlserverhost.local:3306

Then alter your settings so the ``DATABASES`` dictionary points at the proxy
address and not at the actual database, restart Ralph and you're done.

The web app creates a new database connection on each request.
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

See above.

My worker leaves too many connections to the database open.
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

See above.


RQ workers
----------

How to check how many tasks are waiting on the queue?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Just install rq-dashboard to control RQ queues::

  $ pip install rq-dashboard

To use it, just run ``rq-dashboard`` from commandline, and fire up browser on port 9181::

  $ rq-dashboard
  Running on http://0.0.0.0:9181/

TCP/IP
------

There are large amounts of sockets in ``TIME_WAIT`` state on the worker machine. What is this?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Sockets that are closed wait for 60 more seconds to handle possible duplicate
packets and ensure the other party received the ACK. For massively concurrent
workers this can lead to tens of thousands of sockets in the ``TIME_WAIT``
state. The worker machines are dedicated to scan the local network so you can
safely shorten keepalive to 5 * 30 seconds and the timeout interval to 10
seconds and by issuing::

$ sysctl -w net.ipv4.tcp_fin_timeout=10
$ sysctl -w net.ipv4.tcp_keepalive_probes=5
$ sysctl -w net.ipv4.tcp_keepalive_intvl=30

Additionally, if you don't use a load balancer on the worker machine, you can
safely recycle ``TIME_WAIT`` sockets::

$ sysctl -w net.ipv4.tcp_tw_reuse=1
$ sysctl -w net.ipv4.tcp_tw_recycle=1

The current number of waiting connections can be checked by::

  $ sudo netstat -natup | grep "^tcp" | wc -l

On a large subnetwork I'm getting ``ipv4: Neighbour table overflow.`` in ``dmesg``.
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Your ARP table is overflowing. Increase the limits::

  $ sudo sysctl -w net.ipv4.neigh.default.gc_thresh3=8192
  $ sudo sysctl -w net.ipv4.neigh.default.gc_thresh2=8192
  $ sudo sysctl -w net.ipv4.neigh.default.gc_thresh1=4096
  $ sudo sysctl -w net.ipv4.neigh.default.base_reachable_time=86400
  $ sudo sysctl -w net.ipv4.neigh.default.gc_stale_time=86400

How to handle ``"No buffer space available"`` errors on sockets?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

See the two above.
