.. _faq:

==========================
Frequently Asked Questions
==========================

Integration
-----------

Can I set up LDAP authentication?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Yes. You will need to install ``django-auth-ldap`` and ``python-ldap`` using
``pip``. Then add LDAP as an authentication backend in ``settings-local.py``::

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
to local ones. For details consult `the official django-auth-ldap documentation
<http://packages.python.org/django-auth-ldap/>`_. For example, connecting to an
Active Directory service might look like this (users need to be in ``_gr_ralph``
to log in, ``_gr_ralph_admin`` gives superuser privileges)::

  import ldap
  from django_auth_ldap.config import LDAPSearch, GroupOfNamesType
  AUTH_LDAP_SERVER_URI = "ldap://activedirectory.domain:389"
  AUTH_LDAP_BIND_DN = "secret"
  AUTH_LDAP_BIND_PASSWORD = "secret"
  AUTH_LDAP_USER_SEARCH = LDAPSearch("DC=organization,DC=internal",
      ldap.SCOPE_SUBTREE, '(&(objectClass=*)(sAMAccountName=%(user)s))')
  AUTH_LDAP_USER_ATTR_MAP = {"first_name": "givenName", "last_name": "sn",
      "email": "mail"}
  AUTH_LDAP_GROUP_SEARCH = LDAPSearch("DC=organization,DC=internal",
      ldap.SCOPE_SUBTREE, '(objectClass=group)')
  AUTH_LDAP_GROUP_TYPE = GroupOfNamesType(name_attr="cn")
  AUTH_LDAP_REQUIRE_GROUP = "CN=_gr_ralph,OU=Other Resources,"\
      "OU=Users-Restricted,DC=organization,DC=internal"
  AUTH_LDAP_USER_FLAGS_BY_GROUP = {
      "is_active": AUTH_LDAP_REQUIRE_GROUP,
      "is_staff": AUTH_LDAP_REQUIRE_GROUP,
      "is_superuser": "CN=_gr_ralph_admin,OU=Other Resources,"\
                      "OU=Allegro-Restricted,DC=organization,"\
                      "DC=internal"
  }
  AUTH_LDAP_ALWAYS_UPDATE_USER = False

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
  mysql> alter table TABLENAME convert to character set utf8 collate utf8_polish_ci;

Rabbit
------

How to check how many tasks are waiting on the queue?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

On the server where Rabbit is running, do::

  $ sudo rabbitmqctl list_queues -p /ralph

This is most useful if you combine it with ``watch`` so it updates on its own
every 2 seconds::

  $ sudo watch rabbitmqctl list_queues -p /ralph

TCP/IP
------

There are large amounts of sockets in ``TIME_WAIT`` state on the worker machine. What is this?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Sockets that are closed wait for 60 more seconds to handle possible duplicate
packets and ensure the other party received the ACK. For massively concurrent
workers this can lead to tens of thousands of sockets in the ``TIME_WAIT``
state. The worker machines are dedicated to scan the local network so you can
safely shorten the timeout interval to 30 seconds by issuing::

  $ sudo sysctl -w net.ipv4.tcp_fin_timeout=30

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
