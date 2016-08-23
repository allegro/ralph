# Ralph API consumption

Ralph exposes many resources and operation through REST-ful WEB API that can be used both for querying the database and populating it with data. Ralph API use
[Django Rest Framework](http://www.django-rest-framework.org/) under the hood, so
every topic related to it should work in Ralph API as well.

## Authentication

Each user has auto-generated personal token for API authentication. You could obtain your token either by visiting your profile page or by sending request to `api-token-auth` enpoint:

    curl -H "Content-Type: application/json" -X POST https://<YOUR-RALPH-URL>/api-token-auth/ -d '{"username": "<YOUR-USERNAME>", "password": "<YOUR-PASSWORD>"}'
    {"token":"79ee13720dbf474399dde532daad558aaeb131c3"}

If you don't have API token assigned, send request to as above - it'll generate you API token automatically.

In each request to API you have to use your API Token Key in request header:

    curl -X GET https://<YOUR-RALPH-URL>/api/ -H 'Authorization: Token <YOUR-TOKEN>'

## API Versioning

Api requires the client to specify the version in the Accept header.

```
Example:
GET /bookings/ HTTP/1.1
Host: example.com
Accept: application/json; version=v1
```

## Output format

Ralph API supports JSON output format (by default) and HTML preview in your browser (go to https://<YOUR-RALPH-URL>/api/ to see preview).

## Available resources

`work in progress`

## HTTP methods

The following methods can be used in the API. Consult the API reference of
specific module for more precise explanation.

| Method | On a collection                  | On a single resource
|--------|----------------------------------|--------------------------------
| GET    | Get full list of resources       | Get resource details
| POST   | Add a new resource               | -
| PUT    | -                                | Edit the resource (you need to provide all data)
| PATCH  | -                                | Edit the resource (you only need to provide changed data)
| DELETE | -                                | Remove the resource


## Get sample resource

Use HTTP GET method to get details of the resource. Example:

`curl https://<YOUR-RALPH-URL>/api/data-center-assets/1/ | python -m json.tool`

results in:

```JSON
{
    "id": 11105,
    "url": "http://127.0.0.1:8000/api/data-center-assets/1/",
    "hostname": "aws-proxy-1.my-dc",
    "status": "used",
    "sn": "12345",
    "barcode": "54321",
    "price": "55500.00",
    "remarks": "Used as proxy to AWS",
    "position": 12,
    "orientation": "front",
    "configuration_path": "/aws_proxy/prod",
    "service_env": {
        "id": 11,
        "url": "http://127.0.0.1:8000/api/service-environments/11/",
        "service": {
            "id": 1,
            "url": "http://127.0.0.1:8000/api/services/1/",
            "name": "AWS Proxy",
            ...
        },
        "environment": {
            "id": 2,
            "url": "http://127.0.0.1:8000/api/environments/2/",
            "name": "prod",
        }
    }
    },
    "model": {
        "id": 168,
        "url": "http://127.0.0.1:8000/api/asset-models/168/",
        "name": "R630",
        "type": "data_center",
        "power_consumption": 1234,
        "height_of_device": 1.0,
        "cores_count": 8,
        "has_parent": false,
        "manufacturer": {
            "id": 33,
            "url": "http://127.0.0.1:8000/api/manufacturers/33/",
            "name": "Dell",
            ...
        },
        ...
    },
    "rack": {
        "id": 15,
        "url": "http://127.0.0.1:8000/api/racks/15/",
        "name": "Rack 123",
        "server_room": {
            "id": 1,
            "url": "http://127.0.0.1:8000/api/server-rooms/1/",
            "name": "Room 1",
            "data_center": {
                "id": 99,
                "url": "http://127.0.0.1:8000/api/data-centers/99/",
                "name": "New York",
            }
        },
        ...
    },
    ...
}
```

Part of response was skipped for readability.

## You can search records by tags:

`curl https://<YOUR-RALPH-URL>/api/data-center-assets/?tag=tag1&tag=tag2 | python -m json.tool`

You will find all records that contain all of the specified tags.

## Save sample resource

PATCH data center asset with data:
```JSON
{
    "hostname": "aws-proxy-2.my-dc",
    "status": "damaged",
    "service_env": 12,
    "licences": [1, 2, 3]
}
```

Notice in this example that:
* to set related object (not-simple, like string or number) just pass it's ID (see service_env)
* to set many of related objects, pass IDs of them in list (see licences)
* you could pass text value for choice fields (status), even if it's stored as number

## Filtering

Ralph API supports multiple query filers:

> You could check possible fields to filter by sending `OPTIONS` request to particular resource (look at `filtering` item).

* filter by (exact) field value (ex. `<URL>?hostname=s1234.local`)
* lookup filters using Django's `__` convention (check [Django Field lookups documentation](https://docs.djangoproject.com/en/1.8/ref/models/querysets/#field-lookups) for details), ex. `<URL>?hostname__startswith=s123` or `<URL>?invoice_date__lte=2015-01-01`
* extended filters - allows to filter for multiple fields using single query param - it's usefull especially for polymorphic models (like `BaseObject`) - for example filtering by `name` param, you'll filter by `DataCenterAsset` hostname, `BackOfficeAssetHostname` etc. Example: `<URL>/base-objects/?name=s1234.local`
* filter by tags using `tag` query param. Multiple tags could be specified in url query. Example: `<URL>?tag=abc&tag=def&tag=123`

> Fields lookups work with extended filters in `BaseObject` too, ex. `<URL>/base-objects/?name__startswith=s123`


## Transitions API

List of available transition for the selected model

```GET /api/data_center/datacenterasset/46/transitions/```

Results in:

```JSON
{
    "count": 2,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 5,
            "url": "<URL>/api/transitions/5/",
            "source": [
                "new",
                "in use",
                "free",
                "damaged",
                "liquidated",
                "to deploy"
            ],
            "target": "Keep orginal status",
            "name": "Change rack",
            "run_asynchronously": true,
            "async_service_name": "ASYNC_TRANSITIONS",
            "model": "<URL>/api/transitions-model/2/",
            "actions": [
                "<URL>/api/transitions-action/22/"
            ]
        },
...
```

List of POST parameters to run transition for transition:

```OPTIONS <URL>/api/virtual/virtualserver/767/transitions/Initialization/```

Results in:

```JSON
{
  "name": "Transition",
  "description": "Transition API endpoint for selected model.\n\nExample:\n    OPTIONS: /api/<app_label>/<model>/<pk>/transitions/<transition_name>\n    or <transiton_id>",
  "renders": [
    "application/json",
    "text/html",
    "application/xml"
  ],
  "parses": [
    "application/json",
    "application/x-www-form-urlencoded",
    "multipart/form-data",
    "application/xml"
  ],
  "actions": {
    "POST": {
      "network_environment": {
        "type": "choice",
        "required": true,
        "read_only": false,
        "label": "Network environment",
        "choices": [
          {
            "display_name": "aa0003bb (testowa)",
            "value": "1"
          },
          {
            "display_name": "Other",
            "value": "__other__"
          }
        ]
      },
	...
```
