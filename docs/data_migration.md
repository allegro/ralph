# Data imports

It is possible to import data from various formats (e.g.: csv, xml, etc.).
It can be achieved by graphical interface (GUI) and command line (CLI).

## CLI import

Example command which imports data could look like this::

    $ ralph importer --skipid --type file ./path/to/DataCenterAsset.csv --model_name DataCenterAsset

or

    $ ralph importer --skipid --type zip ./path/to/exported-files.zip

To see all available importer options use:

    $ ralph importer --help

## GUI import

(TODO)
