.. _api:

API
====

Ralph provides RESTful API.

Actual version API: **v0.9**

Authentication
--------------

The request to API must include your ``username`` and ``api_key``, example::

    &username=your_username&api_key=your_api_key

Output format
-------------
Using the API you have the possibility to download the data in different formats:

* json
* jsonp
* xml
* yaml

If you want to change the format of the data, you must to add parameter ``format`` to request, example::

    &format=jsonp

.. _cmdb_resources:

CMDB available resources
------------------------

+-------------------------------------+--------------------------------------------------+
|  Resource                           |      Description                                 |
+=====================================+==================================================+
| :ref:`businessline`                 | returns a list of CI's whose type is a service   |
+-------------------------------------+--------------------------------------------------+
| :ref:`ci`                           | returns a list of CI                             |
+-------------------------------------+--------------------------------------------------+
| :ref:`cichange`                     | returns a list of change on CI                   |
+-------------------------------------+--------------------------------------------------+
| :ref:`cichangegit`                  | returns a list of change in GIT repository       |
+-------------------------------------+--------------------------------------------------+
| :ref:`cichangepuppet`               | returns a list of change from Puppet             |
+-------------------------------------+--------------------------------------------------+
| :ref:`cichangezabbixtrigger`        | returns a list of change from Zabbix             |
+-------------------------------------+--------------------------------------------------+
| :ref:`cichangecmdbhistory`          | returns a list of changeshistory on CI           |
+-------------------------------------+--------------------------------------------------+
| :ref:`cilayers`                     | returns a list of all available layers CI's      |
+-------------------------------------+--------------------------------------------------+
| :ref:`ciowners`                     | returns a list of all owners                     |
+-------------------------------------+--------------------------------------------------+
| :ref:`cirelations`                  | returns relationships between CI's               |
+-------------------------------------+--------------------------------------------------+
| :ref:`citypes`                      | returns a list of all available types CI's       |
+-------------------------------------+--------------------------------------------------+
| :ref:`service`                      | returns a list of CI's whose type is a service   |
+-------------------------------------+--------------------------------------------------+

.. _businessline:

BUSINESSLINE
~~~~~~~~~~~~

- **link** ::

    http://localhost:8000/api/v0.9/businessline/

- HTTP Methods
    * GET

- **example returned data** ::

    {
       "meta":{
          "limit":1,
          "next":"/api/v0.9/businessline/?username=username&limit=2&format=json&api_key=api_key",
          "offset":0,
          "previous":null,
          "total_count":10
       },
       "objects":[
          {
             "added_manually":false,
             "barcode":null,
             "business_service":false,
             "cache_version":0,
             "created":"2012-08-20T16:02:14",
             "id":"777",
             "modified":"2012-08-20T16:02:14",
             "name":"Financial services",
             "object_id":1,
             "pci_scope":false,
             "resource_uri":"/api/v0.9/businessline/777/",
             "state":2,
             "status":2,
             "technical_service":true,
             "uid":"bl-1",
             "zabbix_id":null
          }
       ]
    }

.. _ci:

CI
~~

- **link** ::

    http://localhost:8000/api/v0.9/ci/

- HTTP Methods
    * GET

- **example returned data** ::

    {
       "meta":{
          "limit":1,
          "next":"/api/v0.9/ci/?username=username&limit=2&format=json&api_key=api_key",
          "offset":0,
          "previous":null,
          "total_count":123
       },
       "objects":[
          {
             "added_manually":false,
             "barcode":"778866",
             "business_service":false,
             "bussiness_owner":[

             ],
             "cache_version":0,
             "created":"2012-08-20T16:02:14",
             "id":"1",
             "layers":[
                {
                   "id":5,
                   "name":"Hardware"
                }
             ],
             "modified":"2012-08-20T16:02:14",
             "name":"local.dc",
             "object_id":24403,
             "pci_scope":false,
             "resource_uri":"/api/v0.9/ci/1/",
             "state":2,
             "status":2,
             "technical_owner":[

             ],
             "technical_service":true,
             "type":{
                "id":2,
                "name":"Device"
             },
             "uid":"dd-123",
             "zabbix_id":null
          }
       ]
    }

**Ability to filter the resource CI**

Availability methods:

- startswith
    - fields ``name, barcode``
- exact
    - fields ``name, barcode, bussiness_owners, layers, pci_scope, type, technical_owners``

Example usage:

- startswith ::

    http://localhost:/api/v0.9/ci/?field_name__startswith=phrase&username=your_username&api_key=your_api_key&format=json

- exact ::

    http://localhost:/api/v0.9/ci/?field_name=phrase&username=your_username&api_key=your_api_key&format=json



.. _cichange:

CICHANGE
~~~~~~~~

- **link** ::

    http://localhost:8000/api/v0.9/cichange/

- HTTP Methods
    * GET

- **example returned data** ::

    {
       "meta":{
          "limit":1,
          "next":"/api/v0.9/cichange/?username=username&limit=2&format=json&api_key=api_key",
          "offset":0,
          "previous":null,
          "total_count":665
       },
       "objects":[
          {
             "cache_version":0,
             "created":"2012-08-20T16:05:43",
             "external_key":"",
             "id":"123",
             "message":"",
             "modified":"2012-08-20T16:05:45",
             "object_id":2,
             "priority":3,
             "registration_type":4,
             "resource_uri":"/api/v0.9/cichange/123/",
             "time":"2012-08-02T09:59:08",
             "type":2
          }
       ]
    }

.. _cichangecmdbhistory:

CICHANGECMDBHISTORY
~~~~~~~~~~~~~~~~~~~

- **link** ::

    http://localhost:8000/api/v0.9/cichangecmdbhistory/

- HTTP Methods
    * GET

- **example returned data** ::

    {
       "meta":{
          "limit":1,
          "next":"/api/v0.9/cichangecmdbhistory/?username=username&limit=2&format=json&api_key=api_key",
          "offset":0,
          "previous":null,
          "total_count":123
       },
       "objects":[
          {
             "cache_version":1,
             "ci":"/api/v0.9/ci/5/",
             "comment":"Record updated.",
             "created":"2012-09-22T03:04:48",
             "field_name":"parent",
             "id":"2",
             "modified":"2012-09-22T03:04:48",
             "new_value":"Rack 666 (Device)",
             "old_value":"None",
             "resource_uri":"/api/v0.9/cichangecmdbhistory/2/",
             "time":"2012-09-22T03:04:48"
          }
       ]
    }

.. _cilayers:

CILAYERS
~~~~~~~~

- **link** ::

    http://localhost:8000/api/v0.9/cilayers/

- HTTP Methods
    * GET

- **example returned data** ::

    {
       "meta":{
          "limit":1,
          "next":"/api/v0.9/cilayers/?username=username&limit=2&format=json&api_key=api_key",
          "offset":0,
          "previous":null,
          "total_count":8
       },
       "objects":[
          {
             "id":"1",
             "name":"Applications",
             "resource_uri":"/api/v0.9/cilayers/1/"
          }
       ]
    }

.. _ciowners:

CIOWNERS
~~~~~~~~

- **link** ::

    http://localhost:8000/api/v0.9/ciowners/

- HTTP Methods
    * GET

- **example returned data** ::

    {
      "meta": {
          "limit": 1,
          "next": "/api/v0.9/ciowners/?username=username&limit=2&format=json&api_key=api_key",
          "offset": 0,
          "previous": null,
          "total_count": 175
      },
      "objects": [
          {
              "cache_version": 0,
              "created": "2012-09-22T16:07:15",
              "email": "john.ralph@ralph.local",
              "first_name": "John",
              "id": "1",
              "last_name": "Ralph",
              "modified": "2012-10-24T12:07:15",
              "resource_uri": "/api/v0.9/ciowner/1/"
          }
      ]
    }

**Ability to filter the resource CIOWNERS**

Availability methods:

- startswith
    - fields ``first_name, last_name, email``
- exact
    - fields ``first_name, last_name, email``

.. _cirelations:

CIRELATIONS
~~~~~~~~~~~

- **link** ::

    http://localhost:8000/api/v0.9/cirelations/

- HTTP Methods
    * GET

- **example returned data** ::

    {
       "meta":{
          "limit":1,
          "next":"/api/v0.9/cirelations/?username=username&limit=2&format=json&api_key=api_key",
          "offset":0,
          "previous":null,
          "total_count":3568
       },
       "objects":[
          {
             "cache_version":0,
             "child":4436,
             "created":"2012-08-20T16:05:42",
             "id":"4444",
             "modified":"2012-08-20T16:05:42",
             "parent":556699,
             "readonly":true,
             "resource_uri":"/api/v0.9/cirelation/4444/",
             "type":2
          }
       ]
    }

.. _citypes:

CITYPES
~~~~~~~

- **link** ::

    http://localhost:8000/api/v0.9/citypes/

- HTTP Methods
    * GET

- **example returned data** ::

    {
       "meta":{
          "limit":1,
          "next":"/api/v0.9/citypes/?username=username&limit=2&format=json&api_key=api_key",
          "offset":0,
          "previous":null,
          "total_count":10
       },
       "objects":[
          {
             "id":"1",
             "name":"Application",
             "resource_uri":"/api/v0.9/citypes/1/"
          }
       ]
    }

.. _cichangegit:

CICHANGEGIT
~~~~~~~~~~~

- **link** ::

    http:/localhost:8000/api/v0.9/cichangegit/

- HTTP Methods
    * GET
    * POST

- **example returned data** ::

    {
       "meta":{
          "limit":1,
          "next":"/api/v0.9/cichangegit/?username=username&limit=2&format=json&api_key=api_key",
          "offset":0,
          "previous":null,
          "total_count":4054
       },
       "objects":[
          {
            "author":"Ralph <ralph@ralph.local>",
            "cache_version":0,
            "changeset":"b263871ac2093d2b658ae4d6096cc756d069f3a9",
            "comment":"Minor improvements",
            "created":"2012-08-20T16:02:15",
            "file_paths":"conf/crontab#modules/test.txt",
            "id":"2178",
            "modified":"2012-08-20T16:02:15",
            "resource_uri":"/api/v0.9/cichangegit/2178/",
            "time":null
          }
       ]
    }

.. _cichangepuppet:

CICHANGEPUPPET
~~~~~~~~~~~~~~

- **link** ::

    http:/localhost:8000/api/v0.9/cichangepuppet/

- HTTP Methods
    * GET
    * POST

- **example returned data** ::

    {
       "meta":{
          "limit":1,
          "next":"/api/v0.9/cichangepuppet/?username=username&limit=2&format=json&api_key=api_key",
          "offset":0,
          "previous":null,
          "total_count":12
       },
       "objects":[
          {
             "cache_version":0,
             "configuration_version":"a9e826a",
             "created":"2012-08-20T16:05:38",
             "host":"ralph.local",
             "id":"2",
             "kind":"apply",
             "modified":"2012-08-20T16:05:39",
             "resource_uri":"/api/v0.9/cichangepuppet/2/",
             "status":"failed",
             "time":"2012-08-02T09:59:08"
          }
       ]
    }

.. _cichangezabbixtrigger:

CICHANGEZABBIXTRIGGER
~~~~~~~~~~~~~~~~~~~~~

- **link** ::

    http:/localhost:8000/api/v0.9/cichangezabbixtrigger/

- HTTP Methods
    * GET
    * POST

- **example returned data** ::

    {
       "meta":{
          "limit":1,
          "next":"/api/v0.9/cichangezabbixtrigger/?username=username&limit=2&format=json&api_key=api_key",
          "offset":0,
          "previous":null,
          "total_count":2
       },
       "objects":[
          {
             "cache_version":0,
             "comments":"add more network card",
             "created":"2012-11-20T00:00:00",
             "description":"overload network",
             "host":"ralph.local",
             "host_id":12,
             "id":"1",
             "lastchange":"no change",
             "modified":"2012-11-20T00:00:00",
             "priority":1,
             "resource_uri":"/api/v0.9/cichangezabbixtrigger/1/",
             "status":2,
             "trigger_id":1
          }
       ]
    }

.. _service:

SERVICE
~~~~~~~

- **link** ::

    http://localhost:8000/api/v0.9/service/

- HTTP Methods
    * GET

- **example returned data** ::

    {
       "meta":{
          "limit":1,
          "next":"/api/v0.9/service/",
          "offset":0,
          "previous":null,
          "total_count":141
       },
       "objects":[
          {
             "added_manually":false,
             "barcode":null,
             "business_line":"Financial services",
             "business_person":"Ralph Kovalsky",
             "business_person_mail":"",
             "business_service":false,
             "cache_version":0,
             "created":"2012-08-20T16:02:14",
             "external_key":"XNX-666",
             "id":"10973",
             "it_person":"John Ron",
             "it_person_mail":"john.r@ralph.local",
             "location":"PL",
             "modified":"2012-08-20T16:02:14",
             "name":"allegro.pl",
             "object_id":1,
             "pci_scope":false,
             "resource_uri":"/api/v0.9/service/10973/",
             "state":"Active",
             "status":2,
             "technical_service":true,
             "uid":"bs-1",
             "zabbix_id":null
          }
       ]
    }


Discovery available resources
-----------------------------

+-------------------------------------+--------------------------------------------------+
|  Resource                           |      Description                                 |
+=====================================+==================================================+
| :ref:`devicewithpricing`            | returns a list of devices with pricing           |
+-------------------------------------+--------------------------------------------------+


.. _devicewithpricing:

DEVICEWITHPRICING
~~~~~~~~~~~~~~~~~

- **link** ::

    http://localhost:8000/api/v0.9/devicewithpricing/

- HTTP Methods
    * GET

- **example returned data** ::

    {
    "meta": {
        "limit": 1,
        "next": "/api/v0.9/devicewithpricing/?username=ralph&api_key=ralph_pass&limit=1&offset=1&format=json",
        "offset": 0,
        "previous": null,
        "total_count": 5408
    },
    "objects": [
        {
            "barcode": "123456789",
            "boot_firmware": null,
            "cache_version": 21,
            "cached_cost": 666.73,
            "cached_price": 170.0725,
            "chassis_position": 123456789,
            "components": [
                {
                    "count": 4,
                    "model": "CPU Quad-Core Xeon 2533MHz, 4-core",
                    "price": 2824,
                    "serial": null
                },
                {
                    "count": 1,
                    "model": "[rack server] HP ProLiant DL360 G6",
                    "price": 6700,
                    "serial": "SN-2334GLBS"
                },
                {
                    "count": 12,
                    "model": "RAM 4096MiB",
                    "price": 228,
                    "serial": null
                },
                {
                    "count": 5,
                    "model": "HP EGSW23FAW SAS 307200MiB, 10000RPM",
                    "price": 0,
                    "serial": "SF#DGD32456354SD"
                },
                {
                    "count": 776,
                    "model": [
                        "software"
                    ],
                    "price": 0,
                    "serial": null
                },
                {
                    "count": 4,
                    "model": "HP DG0353GE SAS 307200MiB, 10000RPM",
                    "price": 0,
                    "serial": "3536GRERGE45"
                },
                {
                    "count": 5,
                    "model": "Speed unknown",
                    "price": 0,
                    "serial": "45645HER343A"
                }
            ],
            "created": "2013-11-13T15:45:31",
            "dc": "DataCenter1",
            "deleted": false,
            "deprecated": false,
            "deprecation_date": "2012-12-01T00:00:00",
            "diag_firmware": null,
            "hard_firmware": null,
            "id": 1,
            "ip_addresses": [
                {
                    "address": "127.0.0.1",
                    "cache_version": 10,
                    "created": "2012-10-05T10:12:00",
                    "device": "/api/v0.9/dev/23/",
                    "hostname": "server_prod1",
                    "http_family": "HP",
                    "id": 23,
                    "is_management": true,
                    "last_plugins": "",
                    "last_puppet": "2012-01-08T07:02:50",
                    "last_seen": "2012-01-08T07:02:50",
                    "modified": "2012-01-09T05:46:37",
                    "number": "1323234",
                    "resource_uri": "/api/v0.9/ipaddress/23/",
                    "snmp_community": null
                }
            ],
            "last_seen": "2012-01-08T07:02:49",
            "management": {
                "address": "127.0.0.1",
                "cache_version": 10,
                "created": "2012-10-05T10:12:00",
                "device": "/api/v0.9/dev/24/",
                "hostname": "mgmt_server1",
                "http_family": "HP",
                "id": 24,
                "is_management": true,
                "last_plugins": "",
                "last_puppet": "2012-01-08T07:02:50",
                "last_seen": "2012-01-08T07:02:50",
                "modified": "2012-01-09T05:46:37",
                "number": "24",
                "resource_uri": "/api/v0.9/ipaddress/24/",
                "snmp_community": null
            },
            "max_save_priority": 200,
            "mgmt_firmware": "MALO 12 Advanced, Jul 16 2012,",
            "model": {
                "cache_version": 1,
                "chassis_size": null,
                "created": "2012-07-11T14:55:06",
                "group": {
                    "cache_version": 0,
                    "created": "2012-09-24T15:19:58",
                    "id": 12,
                    "modified": "2012-09-24T15:19:58",
                    "name": "HP ProLiant DL360 G6",
                    "price": 9999,
                    "resource_uri": "/api/v0.9/modelgroup/12/",
                    "slots": 0,
                    "type": 201
                },
                "id": 3856220,
                "modified": "2012-07-12T13:56:40",
                "name": "HP ProLiant DL360 G6",
                "resource_uri": "/api/v0.9/model/323/",
                "type": 201
            },
            "modified": "2013-03-19T13:25:03",
            "name": "prod_server1",
            "name2": "test",
            "position": "44",
            "price": null,
            "properties": [],
            "purchase_date": "2009-12-01T00:00:00",
            "rack": "Rack 666",
            "remarks": "Test remarks",
            "resource_uri": "/api/v0.9/devicewithpricing/1/",
            "role": {
                "cache_version": 123,
                "created": "2012-06-19T13:02:31",
                "id": 666,
                "modified": "2012-10-15T14:28:50",
                "name": "www",
                "parent": null,
                "path": "www",
                "resource_uri": "/api/v0.9/role/666/",
                "venture": "/api/v0.9/venture/12/"
            },
            "save_priorities": "hard_firmware=200 model_id=53 support_kind=200 margin_kind_id=200 verified=200 deleted=200 venture_id=200 chassis_position=200 barcode=200 diag_firmware=200 boot_firmware=200 remarks=200 position=200 support_expiration_date=200 venture_role_id=200 last_seen=53",
            "sn": "26234672SHSD",
            "splunk": {
                "splunk_daily_cost": 0,
                "splunk_monthly_cost": 0,
                "splunk_size": 0
            },
            "support_expiration_date": null,
            "support_kind": null,
            "total_cost": 7859.073,
            "uptime_seconds": 2348929,
            "uptime_timestamp": "2011-01-08T07:02:50",
            "venture": {
                "cache_version": 999,
                "created": "2012-10-12T17:13:09",
                "department": {
                    "id": 1,
                    "name": "Infrastrukture",
                    "resource_uri": "/api/v0.9/department/1/"
                },
                "id": 65,
                "is_infrastructure": true,
                "modified": "2012-06-14T13:10:33",
                "name": "Infrastrukture",
                "path": "inf",
                "resource_uri": "/api/v0.9/venture/65/",
                "show_in_ralph": true,
                "symbol": "inf"
            },
            "verified": false,
            "warranty_expiration_date": null
            }
        ]
    }

- **Splunk cost**:

  This resource contains a Splunk cost from last 31 days. If you want have other date range you must use additional parameters:

    * ``splunk_start`` - define a start of date
    * ``splunk_end`` - define a end of datet

  ``splunk_start`` and ``splunk_end`` value must be in format ``Y-m-d`` (example 2012-01-24)
