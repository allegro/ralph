.. _api:

API
====

Various components of ralph suite  expose a REST-ful API that can be used
both for querying the database and populating it with data. The API utilises
tastypie_ to handle your requests. ``json``, ``xml``, ``yaml`` 
or ``plist`` format can be used for data serialization and deserialization.

.. _tastypie: http://django-tastypie.readthedocs.org/en/latest/

Current version of the API: **v0.9**. The API specification is unstable now.

.. _authentication:

Authentication
-----------------

To authenticate yourself you need to provide your ApiKey in a header::

    Authorization: ApiKey your_username:your_api_key

In order to obtain the api_key:

1. Click your username in the lower right corner of the application.
2. Choose "My API key" from the menu.

.. _output_format:

Output format
-------------

There are two ways of setting the format of output:

1. By setting the ``Accept`` header to the correct MIME-type:
2. By adding a ``format`` parameter with the desired format name

+-------------+-------------------------+
| Format name | Mimetype                |
+=============+=========================+
| ``json``    | ``application/json``    |
+-------------+-------------------------+
| ``xml``     | ``application/xml``     |
+-------------+-------------------------+
| ``yaml``    | ``text/xyaml``          |
+-------------+-------------------------+
| ``plist``   | ``application/x-plist`` |
+-------------+-------------------------+

NOTE: In order to use ``plist`` format you need to install `biplist`_ package
which is currently not installed by default in ralph distribution.

.. _biplist: https://pypi.python.org/pypi/biplist

.. _input_format:

Input format
-------------------------

You can use any of the above formats for input. The ``Content-Type`` header
should be set as above.

.. _http_methods:

HTTP methods
-------------------------

The following methods can be used in the API. Consult the API reference of
specific module for more precise explanations. 

+--------+----------------------------------+--------------------------------+
| Method | On a collection                  | On a single resource           |
+========+==================================+================================+
| GET    | Get full list of resources       | Get resource details           |
+--------+----------------------------------+--------------------------------+
| POST   | Add a new resource               | Unused                         |
+--------+----------------------------------+--------------------------------+
| PUT    | Replace the whole collection (!) | Edit the resource (you need to |
|        |                                  | provide all data)              |
+--------+----------------------------------+--------------------------------+
| PATCH  | Unused                           | Edit the resource (you only    |
|        |                                  | need to provide changed data)  |
+--------+----------------------------------+--------------------------------+
| DELETE | Remove the whole collection (!)  | Remove the resource            |
+--------+----------------------------------+--------------------------------+

.. _notes:

Some notes
-----------------------------------------

#. When using the POST method you should expect to receive HTTP status 201
   response. This response will contain ``Location`` header with the URL
   of the created resource. The response body would be empty.
#. The related resource will be specified in one of two ways:

   #. The URL of the related resource
   #. As the details

   You may use any of these in input.


API references for modules:


:ref:`cmdb_resources`


Discovery available resources
-----------------------------

+-------------------------------------+--------------------------------------------------+
|  Resource                           |      Description                                 |
+=====================================+==================================================+
| :ref:`devicewithpricing`            | A collection of of devices with pricing          |
+-------------------------------------+--------------------------------------------------+


.. _devicewithpricing:

DEVICEWITHPRICING
~~~~~~~~~~~~~~~~~

Example
^^^^^^^^^^^^^^^^^^

+---------+------------------------------------------------------------------------------+
| method  | GET                                                                          |
+---------+------------------------------------------------------------------------------+
| URL     | http://localhost:8000/api/v0.9/devicewithpricing?limit=1                     |
+---------+------------------------------------------------------------------------------+
| headers | Accept: application/json                                                     |
|         | Authorization: ApiKey:your_api_key                                           |
+---------+------------------------------------------------------------------------------+

Returned data::

    {
    "meta": {
        "limit": 1,
        "next": "/api/v0.9/devicewithpricing/?limit=1&offset=1",
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
