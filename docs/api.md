# Ralph API consumption

Ralph exposes many resources and operation through REST-ful WEB API that can be used both for querying the database and populating it with data. Ralph API use
[Django Rest Framework](http://www.django-rest-framework.org/) under the hood, so
every topic related to it should work in Ralph API as well.

## Authentication

Each user has auto-generated personal token for API authentication. You could obtain your token either by visiting your profile page or by sending request to `api-token-auth` enpoint:

    curl -X  POST https://<YOUR-RALPH-URL>/api-token-auth/ -d '{"username": "<YOUR-USERNAME>", "password": "<YOUR-PASSWORD>"}'
    {"token":"79ee13720dbf474399dde532daad558aaeb131c3"}

If you don't have API token assigned, send request to as above - it'll generate you API token automatically.

In each request to API you have to use your API Token Key in request header:

    curl -X GET https://<YOUR-RALPH-URL>/api/ -H 'Authorization: Token <YOUR-TOKEN>'

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
