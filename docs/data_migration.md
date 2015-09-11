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

## Migrations from Ralph 2<a name="migration_ralph2"></a>

Our generic importer / exporter allows you to easily export and import all your
data from Ralph 2.

First of all export all your data from Ralph 2:

    $ (ralph) ralph export_model ralph2.zip

This will export all available models to csv files and store them in ralph2.zip
file in current directory.

Then import this zip file to Ralph NG:

    $ (ralph-ng) ralph importer --skipid --type zip ralph2.zip

Notice that `--skipid` option is very important - it'll skip existing Ralph 2
IDs and assign new ones in Ralph NG.

In case of import error, fix data problems on Ralph side (for example missing
field value which is required in Ralph NG), clean your NG database and repeat
import again. To clear database you could run following command:

    $ (ralph-ng) ralph flush && ralph migrate

