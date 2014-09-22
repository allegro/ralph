API
======

.. _cmdb_resources:

CMDB available resources
------------------------

+------------------------------+-----------------------------------------+
|  Resource                    |  Description                            |
+==============================+=========================================+
| :ref:`businessline`          |  list of CI's whose type is a service   |
+------------------------------+-----------------------------------------+
| :ref:`ci`                    |  list of CI                             |
+------------------------------+-----------------------------------------+
| :ref:`cichange`              |  list of change on CI                   |
+------------------------------+-----------------------------------------+
| :ref:`cichangegit`           |  list of change in GIT repository       |
+------------------------------+-----------------------------------------+
| :ref:`cichangepuppet`        |  list of change from Puppet             |
+------------------------------+-----------------------------------------+
| :ref:`cichangezabbixtrigger` |  list of change from Zabbix             |
+------------------------------+-----------------------------------------+
| :ref:`cichangecmdbhistory`   |  list of changeshistory on CI           |
+------------------------------+-----------------------------------------+
| :ref:`cilayers`              |  list of all available layers CI's      |
+------------------------------+-----------------------------------------+
| :ref:`ciowners`              |  list of all owners                     |
+------------------------------+-----------------------------------------+
| :ref:`cirelations`           |  relationships between CI's             |
+------------------------------+-----------------------------------------+
| :ref:`citypes`               |  list of all available types CI's       |
+------------------------------+-----------------------------------------+
| :ref:`service`               |  list of CI's whose type is a service   |
+------------------------------+-----------------------------------------+

.. _ci:

CI
~~~~~~~~~~~~

Retrieving
..............................


To get a list of all CIs, issue a GET request

Example
^^^^^^^^^^^^^^^

+---------+--------------------------------------------------+
| method  | GET                                              |
+---------+--------------------------------------------------+
| URL     | http://localhost:8000/api/v0.9/ci/?limit=1       |
+---------+--------------------------------------------------+
| headers | Accept: application/json                         |
|         |                                                  |
|         | Authorization: ApiKey your_username:your_api_key |
+---------+--------------------------------------------------+

The above request will return:

.. code-block:: json

    {
       "meta":{
          "limit":1,
          "next":"/api/v0.9/ci/?&limit=2",
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

Filtering
^^^^^^^^^^^^^^^^^^

Available parameters: 

startswith
    fields: ``name, barcode``

exact
    fields: ``name, barcode, bussiness_owners, layers, pci_scope, type, technical_owners``

Example usage:

startswith 
    ``http://localhost:/api/v0.9/ci/?field_name__startswith=phrase&username=your_username&api_key=your_api_key``

exact
    ``http://localhost:/api/v0.9/ci/?field_name=phrase&username=your_username&api_key=your_api_key``

Adding
.............................................

To add a new CI issue a POST request to ``/api/v0.9/ci/``

Example:

+---------+-----------------------------------------------------------------------+
| method  | POST                                                                  |
+---------+-----------------------------------------------------------------------+
| URL     | http://ralph.example.com/api/v0.9/ci/                                 |
+---------+-----------------------------------------------------------------------+
| headers | Accept: application/json                                              |
|         |                                                                       |
|         | Content-Type: application/json                                        |
|         |                                                                       |
|         | Authorization: ApiKey your_username:your_api_key                      |
+---------+-----------------------------------------------------------------------+

Request body:

.. code-block:: json

  {
    "added_manually": false,
    "attributes": [
      {
        "name": "Coolness",
        "value": 1
      }
    ],
    "barcode": "zzzzaaabbb",
    "business_owners": [
        "/api/v0.9/ciowners/15/"
    ],
    "business_service": false,
    "cache_version": 0,
    "created": "2012-08-20T16:02:14",
    "layers": [
      "/api/v0.9/cilayers/5/"
    ],
    "modified": "2012-08-20T16:02:14",
    "name": "DC2",
    "object_id": 24405,
    "pci_scope": false,
    "resource_uri": "/api/v0.9/ci/2/",
    "state": 2,
    "status": 2,
    "technical_owners": [
           "/api/v0.9/ciowners/16/",
           "/api/v0.9/ciowners/4/"
    ],
    "technical_service": true,
    "type": "/api/v0.9/citypes/2/",
    "uid": "man-2440534",
    "zabbix_id": null
  }

On success, the above request will return a response with empty body,
status 201 and i.a. this header::

    Location: http://ralph.example.com/api/v0.9/ci/3/

Editing
.............................................

First example - PUT
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

+---------+-----------------------------------------------------------------------+
| method  | PUT                                                                   |
+---------+-----------------------------------------------------------------------+
| URL     | http://ralph.example.com/api/v0.9/ci/3                                |
+---------+-----------------------------------------------------------------------+
| headers | Accept: application/json                                              |
|         |                                                                       |
|         | Content-Type: application/json                                        |
|         |                                                                       |
|         | Authorization: ApiKey your_username:your_api_key                      |
+---------+-----------------------------------------------------------------------+

Request body:

.. code-block:: json

    {
      "added_manually": false,
      "attributes": [
        {
          "name": "Coolness",
          "value": 1
        }
      ],
      "barcode": "zzzzaaabbb",
      "business_owners": [
          "/api/v0.9/ciowners/15/"
      ],
      "business_service": false,
      "cache_version": 0,
      "created": "2012-08-20T16:02:14",
      "layers": [
        "/api/v0.9/cilayers/5/"
      ],
      "modified": "2012-08-20T16:02:14",
      "name": "DC2",
      "object_id": 24405,
      "pci_scope": false,
      "resource_uri": "/api/v0.9/ci/2/",
      "state": 2,
      "status": 2,
      "technical_owners": [
             "/api/v0.9/ciowners/16/"
      ],
      "technical_service": true,
      "type": "/api/v0.9/citypes/2/",
      "uid": "man-2440534",
      "zabbix_id": null
    }

The above request will edit the whole CI. On success the response will have
HTTP status 204

Example 2 - PATCH
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

+---------+-----------------------------------------------------------------------+
| method  | PATCH                                                                 |
+---------+-----------------------------------------------------------------------+
| URL     | http://ralph.example.com/api/v0.9/ci/3                                |
+---------+-----------------------------------------------------------------------+
| headers | Accept: application/json                                              |
|         |                                                                       |
|         | Content-Type: application/json                                        |
|         |                                                                       |
|         | Authorization: ApiKey your_username:your_api_key                      |
+---------+-----------------------------------------------------------------------+

Request body:

.. code-block:: json

    {
      "business_owners": [
          "/api/v0.9/ciowners/15/",
          "/api/v0.9/ciowners/1/",
          "/api/v0.9/ciowners/2/",
          "/api/v0.9/ciowners/3/"
      ]
    }

The above request will change the business owners of a CI, and leave other
data unchanged. On success it will return HTTP status 202.

Editing relations via CI endpoint
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In API v0.10 you can edit relations and filter by related CIs:

The CIs are retrieved and edited with ``related`` field in ci:

.. code-block:: json

    "related": [
        {
            "ci": "/api/v0.10/ci/1/",
            "dir": "OUTGOING",
            "type": "CONTAINS"
        }, {
            "ci": "/api/v0.10/ci/3/",
            "dir": "INCOMING",
            "type": "HASROLE"
        }
    ]

To search for children or parent of a given CI, you need to specify the CI id
as ``child`` or ``parent`` e.g. ``/api/v0.10/ci/?child=1&child=10``.

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



