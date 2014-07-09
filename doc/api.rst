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


