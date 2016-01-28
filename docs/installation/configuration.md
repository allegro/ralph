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

