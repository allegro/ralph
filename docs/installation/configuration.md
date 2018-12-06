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
  "email": "mail",
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

If you nest one LDAP group in another and want to use such (parent) group
in Ralph, you have to define this mapping in ``AUTH_LDAP_NESTED_GROUPS`` and set ``AUTH_LDAP_QUERY_PAGE_SIZE`` setting:

```python3
AUTH_LDAP_NESTED_GROUPS = {
  'CN=_gr_ralph_users,OU=Other,DC=mygroups,DC=domain': "staff",  # _gr_ralph_users contains other LDAP groups inside
}
AUTH_LDAP_QUERY_PAGE_SIZE = 500  # Note that LDAP default page size limit is 1000
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
special meanings. For example users need to be in ``active`` to log in,
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

# Synchronization with OpenStack

Ralph 3 supports one-way synchronization with OpenStack. It is possible to
download data from OpenStack including projects and instances. All the
synchronized data will be available in Ralph in read-only mode. It will be
possible only to change the _Service Environment_, _Tags_ and _Remarks_ fields.

**Note**: _Service Environment_ of a _CloudHost_ is inherited from a
_Cloud Project_ to which it belongs.

## Installation

To enable openstack_sync plugin you will have to install python requirements
by executing: ``pip install -r requirements/openstack.txt``

It is also necessary to add your _OpenStack_ instances configuration to your
local settings.
Example configuration should look as follows:
```python3
OPENSTACK_INSTANCES = [
    {
        'username':     'someuser',
        'password':     'somepassword',
        'tenant_name':  'admin',
        'version':      '2.0',
        'auth_url':     'http://1.2.3.4:35357/v2.0/',
        'tag':          'someinfo'
    },
    {
    ... another instance ...
    }
]
```

``someuser:`` is an OpenStack user which has permissions to list all the
projects/tenants and instances

``tenant_name:`` project/tenant to which the user will authenticate

``version:`` version of OpenStack API. Currently only **API 2.x** is
supported

``auth_url:`` address, where OpenStack API is available

``tag:`` this is a tag that will be added to each _Cloud Projects_ and _Cloud
Hosts_ migrated from OpenStack

You can add multiple _OpenStack_ instances by adding another _python dict_ to
_OPENSTACK_INSTANCES_ list.

## How to execute

You can either run the script manually by executing: ``ralph openstack_sync``
or you can add it to _corntab_.

First execution will add all the _Cloud Projects_, _Cloud Hosts_ and _Cloud
Flavors_ from _OpenStack_ to _Ralph_. Following executions will add and modify
data as well as delete all the objects which no longer exists in configured
OpenStack Instances.
