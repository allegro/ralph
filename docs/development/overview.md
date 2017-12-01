# Finding your way around the sources

## Concept

The entire application is based on highly operational django models. Django framework generates user interface forms on its own. As simplicity is our main concern, we prefer to keep the models fat and user interface thin. That's why we rely on Django admin panel for managing user interface.

## Main modules

Ralph is divided into separate models, such as:
* Assets - storing a wide array of information about fixed assets
* Scan - discovering equipment of data centres
* Licenses - managing licenses for both software and hardware
* CMDB - configuration management database

Note: help us improve this documentation ! :-)
