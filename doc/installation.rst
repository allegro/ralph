==============
How to install
==============

.. note::  

   You can install Ralph on a variety of sensible operating systems. This guide
   assumes Ubuntu Server 12.04 LTS and presents shell command examples
   accordingly.  MySQL as the relational backend for Django is also assumed but
   other databases supported by Django may be used as well. ``sqlite3`` is
   discouraged for larger deployments because it doesn't support concurrent
   writes which are very common on a distributed queue-based architecture.
   
   **If you happen to use another setup**, please take a moment to write down
   what you were doing and send it over. This way we can add examples for your
   system as well.

Installing Python
-----------------

Ralph requires Python 2.7 which is included in the latest Ubuntu Server 12.04
systems::

  $ sudo apt-get install python-dev python-virtualenv

During the installation, Ralph builds a set of required dependencies. This
requires a sensible building environment available::

  $ sudo apt-get install build-essential libbz2-dev libfreetype6-dev libgdbm-dev
  $ sudo apt-get install libjpeg-dev libldap2-dev libltdl-dev libmemcached-dev
  $ sudo apt-get install libmysqlclient-dev libreadline-dev libsasl2-dev libsqlite3-dev
  $ sudo apt-get install libssl-dev libxslt1-dev ncurses-dev zlib1g-dev

setcap
~~~~~~

One of the things Ralph does is pinging addresses to tell whether they are used
by machines inside the network. Ping works by ICMP which basically requires
access to raw sockets. By design these sockets can only be opened by *root*. The
``ping`` tool uses the *setuid* bit because of that reason. Marking the
``python`` binary with *setuid* would create a massive security hole which is
why another approach is necessary: ``setcap``.

``setcap`` is a tool that sets `file capabilities
<http://www.kernel.org/doc/man-pages/online/pages/man7/capabilities.7.html>`_.
For Ubuntu Server it is available by installing::

  $ sudo apt-get install libcap2-bin

The capability we're after is ``CAP_NET_RAW`` which enables a binary to use raw
and packet sockets. To enable this for every system user, type::

  $ sudo setcap cap_net_raw=ep /usr/bin/python2.7

Please note that we set caps directly on the binary (e.g. **not on a symlink**).

Message queue
-------------

Ralph works in a distributed fashion, communication between worker nodes happens
through a central queue. For evaluation purposes and simple installations, the
default is to use an SQLite database which requires no configuration. For larger
deployments we strongly recommend either `Redis <http://redis.io/>`_ or
`RabbitMQ <http://www.rabbitmq.com/>`_ as the broker.

Redis
~~~~~

We like to use ``Redis`` as the message broker because of its performance and
simplicity. We require **at least version 2.2** because of our use of list
commands which were added in that version. Ubuntu Server 12.04 LTS delivers::

  $ sudo apt-get install redis-server

Since lost tasks can always be sent again, the durability guarantees which Redis
provides by default are not necessary. You can significantly speed up the queue
by commenting out the ``save`` lines from ``/etc/redis/redis.conf``.

We can check the status of the Redis server::

  $ redis-cli -h localhost -p 6379 -n 0 info
  redis_version:2.2.12
  redis_git_sha1:00000000
  redis_git_dirty:0
  arch_bits:64
  multiplexing_api:epoll
  process_id:22698
  uptime_in_seconds:50
  uptime_in_days:0
  lru_clock:167
  used_cpu_sys:0.02
  used_cpu_user:0.00
  used_cpu_sys_children:0.00
  used_cpu_user_children:0.00
  connected_clients:1
  connected_slaves:0
  client_longest_output_list:0
  client_biggest_input_buf:0
  blocked_clients:0
  used_memory:798824
  used_memory_human:780.10K
  used_memory_rss:1429504
  mem_fragmentation_ratio:1.79
  use_tcmalloc:0
  loading:0
  aof_enabled:0
  changes_since_last_save:0
  bgsave_in_progress:0
  last_save_time:1342178903
  bgrewriteaof_in_progress:0
  total_connections_received:2
  total_commands_processed:3
  expired_keys:0
  evicted_keys:0
  keyspace_hits:0
  keyspace_misses:1
  hash_max_zipmap_entries:512
  hash_max_zipmap_value:64
  pubsub_channels:0
  pubsub_patterns:0
  vm_enabled:0 role:master

.. note::

  Remember to configure redis in `settings.py <configuration.html#message-queue-broker>`_.

rabbitmq
~~~~~~~~

Alternatively, ``rabbitmq`` can be used as a production-grade message broker for
Ralph tasks.  We require **at least version 2.5** because earlier implementation
didn't handle running out of physical memory well. Ubuntu Server 12.04 LTS ships
a sensible version, we can simply ``apt-get`` it::

  $ sudo apt-get install rabbitmq-server

Once it's installed, we should remove the default ``guest`` account and replace
it with a dedicated one (replace ``$PASSWORD`` with a password of your choice)::

  $ sudo rabbitmqctl delete_user guest
  $ sudo rabbitmqctl add_user ralph $PASSWORD
  $ sudo rabbitmqctl add_vhost /ralph
  $ sudo rabbitmqctl set_permissions -p /ralph ralph ".*" ".*" ".*"

By default, Rabbit listens on port *5672* which can also be customized::

  $ sudo sh -c 'echo "NODE_PORT=5672" >> /etc/rabbitmq/rabbitmq-env.conf'
  $ sudo /etc/init.d/rabbitmq-server restart

Finally we can check the status of the newly configured server::

    $ sudo rabbitmqctl status
    Status of node rabbit@s10821 ...
    [{pid,29097},
    {running_applications,[{rabbit,"RabbitMQ","2.4.1"},
                            {mnesia,"MNESIA  CXC 138 12","4.4.12"},
                            {os_mon,"CPO  CXC 138 46","2.2.4"},
                            {sasl,"SASL  CXC 138 11","2.1.8"},
                            {stdlib,"ERTS  CXC 138 10","1.16.4"},
                            {kernel,"ERTS  CXC 138 10","2.13.4"}]},
    {nodes,[{disc,[rabbit@s10821]}]},
    {running_nodes,[rabbit@s10821]}]
    ...done.

Database 
--------

In theory, any database server supported by the Django ORM may be used with
Ralph. The default configuration uses SQLite which is enough for evaluation
purposes and small deployments.

We use and support MySQL. You will need **at least version 5.5** because it
provides multiple rollback segments which are required to maintain sensible
performance with more than a handful of workers. Installation::

  $ sudo apt-get install mysql-server libmysqlclient-dev libmysqld-dev

Once it's up and running let's set some stuff up::

  $ mysqladmin -u root -p create ralph
  $ mysql -u root -p
  mysql> alter database ralph character set utf8 collate utf8_polish_ci;
  mysql> use mysql;
  mysql> update user set password=password("rootpw") where user='root';
  mysql> create user 'ralph'@'localhost' identified by 'ralph';
  mysql> grant all privileges on ralph.* to 'ralph'@'localhost';
  mysql> flush privileges;
  mysql> quit
  $ sudo service mysql restart

Caching
-------

For small deployments the built-in in-memory cache provided by Django is enough.
For larger setups we strongly recommend Memcached::

  $ sudo apt-get install memcached

Apache
------

To use Apache as the front-end Web server for Ralph, install it::

  $ sudo apt-get install apache2-mpm-worker libapache2-mod-proxy-html
  $ sudo a2enmod proxy
  $ sudo a2enmod proxy_http

Now add the Ralph site configuration to `/etc/apache2/sites-enabled/ralph
<_static/apache>`_, restart Apache and you're done. Alternatively, you can
check out `configuration for usage with modwsgi <_static/apache-wsgi>`_ (you
will need the `ralph.wsgi <_static/ralph.wsgi>`_ file, too).

.. note::

  Remember to adapt the project and static paths in the Apache configuration
  files to fit your actual system configuration.

Ralph
-----

system user
~~~~~~~~~~~

Unprivileged and not owned by a person::

  $ sudo adduser --home /home/ralph ralph
  $ sudo su - ralph

virtual environment
~~~~~~~~~~~~~~~~~~~

Let's create a virtual environment for Python in the user's home::

  $ virtualenv . --distribute --no-site-packages

The newly created virtual environment contains a directory structure mimicking
``/usr/local``::

  $ tree -dL 3
  .
  ├── bin
  ├── include
  │   └── python2.7 -> /usr/local/include/python2.7
  └── lib
      └── python2.7
          ├── config -> /usr/local/lib/python2.7/config
          ├── distutils
          ├── encodings -> /usr/local/lib/python2.7/encodings
          ├── lib-dynload -> /usr/local/lib/python2.7/lib-dynload
          └── site-packages

  10 directories

In any shell the user can *activate* the virtual environment. By doing that, the
default Python executable and helper scripts will point to those within the
virtual env directory structure::

  $ which python
  /usr/local/bin/python
  $ . bin/activate
  (ralph)$ which python
  /home/ralph/bin/python

To automate this it's very useful to add ``source /home/ralph/bin/activate`` to
``/home/ralph/.profile`` or ``/home/ralph/.bashrc``. That way with each login
the virtual environment is activated and the user doesn't have to remember to do
that.

**Further setup assumes an activated virtual environment.** 

.. note::
  
  You also have to call ``setcap`` on the Python binary created in the
  virtualenv's ``bin`` directory::

    $ sudo setcap cap_net_raw=ep /home/ralph/bin/python

Installing from pip
~~~~~~~~~~~~~~~~~~~

Simply invoke::

  (ralph)$ pip install ralph

That's it.

Installing from sources
~~~~~~~~~~~~~~~~~~~~~~~

Alternatively, to live on the bleeding edge, you can clone the Ralph git
repository to ``project`` and install it manually::

  (ralph)$ git clone git://github.com/allegro/ralph.git project
  (ralph)$ cd project
  (ralph)$ pip install -e .

The last command will install numerous dependencies to the virtual environment
we just created. It's important that we used an activated virtual environment
because without it, the dependencies would install directly in
``/usr/local/lib/python2.7/site-packages/`` which could potentially create
compatibility problems for other applications requiring other versions of the
dependencies installed.

.. note::

  If your PIL installation on Ubuntu 12.04 ends up telling::

      *** TKINTER support not available
      *** JPEG support not available
      *** ZLIB (PNG/ZIP) support not available
      *** FREETYPE2 support not available
      *** LITTLECMS support not available

  you should try running::

      $ sudo apt-get install libjpeg8-dev liblcms1-dev libpng12-dev
      $ pushd /usr/lib
      $ sudo ln -s x86_64-linux-gnu/libz.so libz.so
      $ sudo ln -s x86_64-linux-gnu/libfreetype.so libfreetype.so
      $ popd
      $ pip install -U Pillow

  Now PIL should at least tell you this much::

      *** TKINTER support not available
      --- JPEG support available
      --- ZLIB (PNG/ZIP) support available
      --- FREETYPE2 support available
      --- LITTLECMS support available

  Note that we are not using the default ``PIL`` package from PyPI but the
  friendly ``Pillow`` fork which is actively maintained by the Plone
  community.

Initial setup
~~~~~~~~~~~~~

Once installed, we can create a configuration file template::

  (ralph)$ ralph makeconf

This will create a ``.ralph/settings`` file in the current user's home
directory. You can also create these settings in ``/etc`` by providing the
``--global`` option to ``makeconf``.

After creating the configuration file, you have to customize it like described
on :ref:`the configuration page <configuration>` so that Ralph knows how to
connect to your database, message broker, etc. You can skip customizing
configuration for strictly evaluation purposes, it will use SQLite and other
zero configuration options.

After creating the default config file, let's synchronize the database from
sources by running the standard ``syncdb`` management command::

  (ralph)$ ralph syncdb

Django will create some tables, setup some default values and ask whether you
want to create a superuser. Do so, you will use the credentials given to test
whether the setup worked. Then migrate the rest of the tables::

  (ralph)$ ralph migrate

Lastly, we need to link the static images, CSS files, JavaScript sources, etc.
to a common place so the front-end Web server can pick them up. That way the
back-end doesn't have to deal with static files. The command to do that is
simple::

  (ralph)$ ralph collectstatic -l

By default the ``collectstatic`` command copies the files. The ``-l`` option
creates symlinks instead.

Testing if it works
-------------------

Finally, there's the most fun part where you have to see why it doesn't work. In
theory it should all run fine, see for yourself.

Python and setcap
~~~~~~~~~~~~~~~~~

From the project directory run::

  $ ralph test util
  Creating test database for alias 'default'...
  ..
  ----------------------------------------------------------------------
  Ran 2 tests in 0.505s

  OK
  Destroying test database for alias 'default'...

Back-end web server
~~~~~~~~~~~~~~~~~~~

From the project directory run::

  (ralph)$ ralph run_gunicorn
  Validating models...
  0 errors found

  Django version 1.3, using settings 'ralph.settings'
  Server is running
  Quit the server with CONTROL-C.
  2011-04-18 13:39:34 [17904] [INFO] Starting gunicorn 0.12.1 2011-04-18
  13:39:34 [17904] [INFO] Listening at: http://127.0.0.1:8000 (17904) 2011-04-18
  13:39:34 [17904] [INFO] Using worker: sync 2011-04-18 13:39:34 [17912] [INFO]
  Booting worker with pid: 17912

The service should be accessible from the localhost. You may invoke this command
with a ``host:port`` argument to see the web app from a remote host. For
production use however, configure a front-end Web server (like Apache described
above) and run Gunicorn as a daemon. You may find example Gunicorn ``init.d``
scripts in the :ref:`FAQ <faq>`.

Message queue
~~~~~~~~~~~~~

From the project directory run::

  (ralph)$ ralph celeryd -l info
  [2011-04-11 14:41:22,958: WARNING/MainProcess]  

  -------------- celery@Macallan.local v2.2.5
  ---- **** -----
  --- * ***  * -- [Configuration]
  -- * - **** ---   . broker:      amqplib://ralph@localhost:25672/ralph
  - ** ----------   . loader:      djcelery.loaders.DjangoLoader
  - ** ----------   . logfile:     [stderr]@INFO
  - ** ----------   . concurrency: 4
  - ** ----------   . events:      OFF
  - *** --- * ---   . beat:        OFF
  -- ******* ----
  --- ***** ----- [Queues]
  --------------   . celery:      exchange:celery (direct) binding:celery
                    
  [Tasks]

  [2011-04-11 14:41:22,970: INFO/PoolWorker-1] child process calling self.run()
  [2011-04-11 14:41:22,971: INFO/PoolWorker-2] child process calling self.run()
  [2011-04-11 14:41:22,972: INFO/PoolWorker-3] child process calling self.run()
  [2011-04-11 14:41:22,975: INFO/PoolWorker-4] child process calling self.run()
  [2011-04-11 14:41:22,977: WARNING/MainProcess] celery@Macallan.local has started.

This runs the worker processes. Leave it open for now, in the next step we'll
check if the communication works alright.

Ralph tasks
~~~~~~~~~~~

First let's try interactively to discover a single host::

  (ralph)$ ralph discover 127.0.0.1
  127.0.0.1... up!

Should the discovery show that 127.0.0.1 is down, check whether your Python
binary has been ``setcap``'ed. Did the ``util`` unit tests succeed?

If everything's alright, let's try to run the discovery remotely::

  $ ralph discover --remote 127.0.0.1
  
This won't return anything on stdout but on your Celeryd console you should
see::

  [2011-04-19 14:44:38,843: INFO/MainProcess] Got task from broker: ralph.discovery.tasks.discover_single[d9eed94e-4741-47a2-b539-91464a17695d]
  [2011-04-19 14:44:38,882: INFO/PoolWorker-64] 127.0.0.1... up!
  [2011-04-19 14:44:38,883: INFO/MainProcess] Task ralph.discovery.tasks.discover_single[d9eed94e-4741-47a2-b539-91464a17695d] succeeded in 0.0220642089844s: True

That's it!
----------

If all of the above worked, you're all set up and ready to do some actual work.
