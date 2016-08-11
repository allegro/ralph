# Deployment

## Introduction

TODO

## Preboot configuration

`Preboot configuration` allows you define custom files being executed during
`Deployment`. Such as `kickstart` or `iPXE`.

To define such `preboot configuration` you need to:
- visit `Preboot configuration` (/deployment/prebootconfiguration/) page
- click "Add preboot configuration"
- on new page there is a form with a few fields, like:

    - Name (This is the name, by which you could reference this `preboot
      configuration` in future)
    - Type (one of these options: 'kickstart`, `iPXE`)
    - Configuration
    - Description


Ad. `Configuration` field:
This field allows you to write `kickstart` (or `iPXE`) configuration.
It's possible to include variables from Ralph. These are:

    - configuration_class_name (eg. 'www')
    - configuration_module (eg. 'ralph')
    - configuration_path (eg. 'ralph/www')
    - dc (eg. 'data-center1')
    - deployment_id (eg. 'ea9ea3a0-1c4d-42b7-a19b-922000abe9f7')
    - domain (eg. 'dc1.mydc.net')
    - done_url (eg. 'http://127.0.0.1:8000/deployment/ea9ea3a0-1c4d-42b7-a19b-922000abe9f7/mark_as_done')
    - hostname (eg. 'ralph123.dc1.mydc.net')
    - initrd (eg. 'http://127.0.0.1:8000/deployment/ea9ea3a0-1c4d-42b7-a19b-922000abe9f7/initrd')
    - kernel (eg. 'http://127.0.0.1:8000/deployment/ea9ea3a0-1c4d-42b7-a19b-922000abe9f7/kernel')
    - kickstart (eg. 'http://127.0.0.1:8000/deployment/ea9ea3a0-1c4d-42b7-a19b-922000abe9f7/kickstart')
    - ralph_instance (eg. 'http://127.0.0.1:8000')
    - service_env (eg. 'Backup systems - prod')
    - service_uid (eg. 'sc-123')

Note:
All above links (like: `http://127.0.0.1:8000/deployment/ea9ea3a0-1c4d-42b7-a19b-922000abe9f7/mark_as_done`)
starts with `http://127.0.0.1:8000`.
This is because default settings is

```
RALPH_INSTANCE = 'http://127.0.0.1:8000'
```

you should customise `RALPH_INSTANCE` variable to fit your set up.


### Example:

This is example of `kickstart` file using one of above variables (`hostname`)
```
lang en_US
langsupport en_US
keyboard us

echo {{ hostname }}
```
