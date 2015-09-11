# Installation guide

For production, we provide both deb package and  docker(compose) image.
We only support Ubuntu 14.04 Trusty distribution.

On the other hand, if you are developer, we strongly suggest using our `Vagrant` inside the `vagrant` directory
with many development *bells and whistles* included.

## Debian/Ubuntu package - recommended

Make sure, your installation is clean Ubuntu 14.04, without any other packages installed.

First, add our official ralph repository:

    sudo apt-key adv --keyserver  hkp://keyserver.ubuntu.com:80 --recv-keys 379CE192D401AB61
    sudo sh -c "echo 'deb https://dl.bintray.com/vi4m/ralph wheezy main' >  /etc/apt/sources.list.d/vi4m_ralph.list"

Then, just install ralph the traditional way:

    sudo apt-get update
    sudo apt-get install ralph-core redis-server mysql-server

Note: Main www instance of Ralph requires redis and mysql server installed. If you want to install only ralph agent somewhere, just install `ralph-core` and point it to the particular mysql and redis instance somewhere on your network.


### Configuration


Create the database.

    > mysql -u root
    > CREATE database ralph default character set 'utf8';

### Settings

We are working on some sane configuration management files.
Currently, we just read some environment variables, so just paste somewhere in your ~/.profile following environment variables customizing it to your needs.

cat ~/.profile

    export DB_ENV_MYSQL_DATABASE=ralph
    export DB_ENV_MYSQL_USER=someuser
    export DB_ENV_MYSQL_PASSWORD=somepassword
    export DB_ENV_MYSQL_HOST=127.0.0.1
    export PATH=/opt/ralph/ralph-core/bin/:$PATH

### Initialization
1. Type `ralph migrate` to create tables in your database.
2. Type `ralph sitetree_resync_apps` to reload menu.
3. Type `ralph createsuperuser` to add new user.

Run your ralph instance with `ralph runserver 0.0.0.0:8000`

Now, point your browser to the http://localhost:8000 and log in. Happy Ralphing!

## Docker installation (experimental)

You can find experimental docker-compose configuration in https://github.com/allegro/ralph/tree/ng/docker directory.
Be aware, it is still a beta.

### Install
Install docker and [docker-compose](http://docs.docker.com/compose/install/) first.


### Create compose configuration
Copy ``docker-compose.yml.tmpl`` outside ralph sources to docker-compose.yml
and tweak it.

### Build
Then build ralph:

    docker-compose build


To initialize database run:

    docker-compose run --rm web /root/init.sh

Notice that this command should be executed only once, at the very beginning.

### Run
Run ralph at the end:

    docker-compose up

Ralph should be accessible at ``http://127.0.0.1`` (or if you are using ``boot2docker`` at ``$(boot2docker ip)``). Documentation is available at ``http://127.0.0.1/docs``.

If you are upgrading ralph image (source code) run:

    docker-compose run --rm web /root/upgrade.sh


# LDAP Authentication

It is possible to enable authentication via various LDAP/AD systems.

You will need to install ``pip install -r requirements/prod_ldap.txt``.
Then add LDAP as an authentication backend in your local settings:

```python3
  AUTHENTICATION_BACKENDS = (
      'django_auth_ldap.backend.LDAPBackend',
      'django.contrib.auth.backends.ModelBackend',
  )
  LOGGING['loggers']['django_auth_ldap'] = {
      'handlers': ['file'],
      'propagate': True,
      'level': 'DEBUG',
  }
```

You will need to configure the LDAP connection as well as mapping remote users
and groups to local ones. For details consult the official django-auth-ldap
documentation [http://packages.python.org/django-auth-ldap](http://packages.python.org/django-auth-ldap).
For example, connecting to an Active Directory service might look like this:

```python3
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
AUTH_LDAP_USER_ATTR_MAP = {
  "first_name": "givenName",
  "last_name": "sn",
  "email": "mail"
  "company": "company",
  "manager": "manager",
  "department": "department",
  "employee_id": "employeeID",
  "location": "officeName",
  "country": "ISO-country-code",
}
```

However, when using OpenDJ as a LDAP server, ``AUTH_LDAP_USER_USERNAME_ATTR`` should be equal to ``uid``:

```python3
AUTH_LDAP_USER_USERNAME_ATTR = "uid"
```

For other implementations objectClass may have the following values:

 * Active Directory: objectClass=user,
 * Novell eDirectory: objectClass=inetOrgPerson,
 * Open LDAP: objectClass=posixAccount

Manager is special field and is treated as reference to another user,
for example "CN=John Smith,OU=TOR,OU=Corp-Users,DC=mydomain,DC=internal"
is mapped to "John Smith" text.

Country is special field, the value of this field must be a country code in the
[ISO 3166-1 alfa-2](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2) format.

Ralph provides ldap groups to django groups mapping. All what you need to
do are:

 * import custom ``MappedGroupOfNamesType``,
 * set up group mirroring,
 * declare mapping.

```python3
from ralph.account.ldap import MappedGroupOfNamesType
AUTH_LDAP_GROUP_MAPPING = {
  'CN=_gr_ralph,OU=Other,DC=mygroups,DC=domain': "staff",
  'CN=_gr_ralph_assets_buyer,OU=Other,DC=mygroups,DC=domain': "assets-buyer",
  'CN=_gr_ralph_assets_helper,OU=Other,DC=mygroups,DC=domain': "assets-helper",
  'CN=_gr_ralph_assets_staff,OU=Other,DC=mygroups,DC=domain': "assets-staff",
  'CN=_gr_ralph_admin,OU=Other,DC=mygroups,DC=domain': "superuser",
}
AUTH_LDAP_MIRROR_GROUPS = True
AUTH_LDAP_GROUP_TYPE = MappedGroupOfNamesType(name_attr="cn")
AUTH_LDAP_GROUP_SEARCH = LDAPSearch("DC=organization,DC=internal",
    ldap.SCOPE_SUBTREE, '(objectClass=group)')
```

Note: For OpenDJ implementation ``AUTH_LDAP_GROUP_MAPPING`` is not obligatory. ``AUTH_LDAP_GROUP_TYPE`` and ``AUTH_LDAP_GROUP_SEARCH`` should be set as follows:

```python3
from django_auth_ldap.config import GroupOfUniqueNamesType
AUTH_LDAP_GROUP_TYPE = GroupOfUniqueNamesType()
AUTH_LDAP_GROUP_SEARCH = LDAPSearch("DC=organization,DC=internal",
  ldap.SCOPE_SUBTREE, '(structuralObjectClass=groupOfUniqueNames)')
```

If you want to define ldap groups with names identical to ralph roles, you
shouldn't declare mapping ``AUTH_LDAP_GROUP_MAPPING``. If there are any one
mapping defined another groups will be filtered. Some groups have
special meanings. For example users need to be in ``staff`` to log in,
``superuser`` gives superuser privileges. You can read more info
in :ref:`groups`.

You can define users filter, if you don't want to import all users to ralph:

```python3
AUTH_LDAP_USER_FILTER = '(|(memberOf=CN=_gr_ralph_group1,OU=something,'\
    'DC=mygroup,DC=domain)(memberOf=CN=_gr_ralph_group2,OU=something else,'\
    'DC=mygroups,DC=domain))'
```

In case of OpenDJ please use ``isMemberOf`` instead of ``memberOf``.

To synchronize user list you must run command:

    $ ralph ldap_sync

During the process, script will report progress on every 100-th item loaded.


# Migration from Ralph 2

If you used Ralph 2 before and want to save all your data see [Migration from Ralph 2 guide](./data_migration.md#migration_ralph2)
