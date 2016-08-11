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

    - configuration_path
    - dc
    - deployment_id
    - domain
    - done_url
    - hostname
    - initrd
    - kernel
    - kickstart
    - ralph_instance
    - service_env


### Example:

This is example of `kickstart` file using one of above variables (`hostname`)
```
lang en_US
langsupport en_US
keyboard us

echo {{ hostname }}
```
