Quickstart
==========

The Ralph Assets module enables management of assets, licences and supports.
Any objects in this modules allows manage relation beetween them.


Assets
^^^^^^

Searching and Filtering of Assets
---------------------------------

Let's start with the main screen. Here you find all your hardware assets which
are in the database. Use the left column for filtering of the assets.

There are two types of assets -- devices and parts. A device could be a blade
server, and a part is a component of this server, for example memory or hard
disk drive. A part can be assigned to a single device at a time. You can move
parts from one device to another when you need it.


Adding Assets
-------------

data center
"""""""""""
If you want add data center asset you need to fill a few required fields.
Look at the screen below (you can zoom-in the image in your browser if you
want) The fields in bold are required. Rest of fields are optional.

.. image:: images/add-data-center-asset-form.png
    :scale: 30%

Let's describe each of the fields:

- **Basic info**:
    - **Type** - a read only field for data center
    - **Model** - choose a model for asset, (you can type a couple of letters
      to search for a given model. If no result is found, just click "Add"
      button to add it)
    - **Inventory number** - an alphanumeric value in your stock
    - **Warehouse** - the place where the asset is located
    - **Location** - a more exact location of the device in the building/room
    - **Status** - an asset's lifetime indicator. Newly bought assets has
      status "new". You can change it as required according to your own work
      flow
    - **Task url** - url to task in ticket system
    - **Additional remarks** - field for various data
    - **Service name** - service name to which this asset belongs
    - **Property of** - company to which this asset belongs
    - **Hostname** - read-only field telling the name of host (from Ralph-core
      device)
    - **Service catalog** - points to ``service catalog`` which asset belongs
      to
    - **Environment** - points to environment which asset belongs to
    - **Region** - set ``region`` for this asset (see ``region`` page for
      details)
- **Financial Info**:
    - **Order number** - number of the order where this asset is included
    - **Invoice date** - date of the invoice where this asset is included
    - **Invoice number** - number of the invoice where this asset is included
    - **Price** - unit price of this asset
    - **Provider** - name of the provider of this asset
    - **Depreciation rate** - number of months in which asset depreciates
    - **Source** - asset was purchased or salvaged
    - **Request date** - date of submission of the demand for this asset
    - **Provider order date** - date when order of this asset was provided
    - **Delivery date** - date of asset delivery
    - **Depreciation end date** - the end day of the depreciation
    - **Budget info** - name of budget which funds this asset
    - **Force depreciation** - force depreciation for this asset despite of
      ``depreciation end date`` value
- **User info**:
    - **User** - points to user of this asset
    - **Owner** - points to a owner of this asset
- **Aditional info**:
    - **Data center** - points to a data center which contains this asset
    - **Server room** - points to a server room which contains this asset
    - **Rack** - points to a rack which contains this asset
    - **Position** - points to position in rack from 0 to 'max u'
    - **Orientation** - a side of rack, depends on ``position``

      if ``position`` = 0 options are: *left*, *right*

      if ``position`` > 0 options are: *front*, *back*, *middle*

    - **Slot number** - points to slot number in *blade* when asset model is
      *blade*
    - **Ralph device id** - points to to Ralph-Core device
    - **Force unlink** - if picked and ``"ralph device id"`` is already linked
      to other asset, this option forces to unlink it and link this asset to
      newly unlinked device
    - **Create stock device** - create a Ralph-core device


back office
"""""""""""
Now, let's add some devices and parts. Click the "Add device" option from the
top of submenu.

.. image:: images/asset_add_device.png
    :scale: 53%

The serial number or barcode field is required for assets.
You can paste serial numbers and barcodes in series,
thus allowing you to batch-add many devices of the same type.


Adding Parts
------------

In the same way you can add parts to the database, and then bind the parts to
devices. To do this, choose "Add part" from the menu.


.. image:: images/asset_add_part.png
    :scale: 55%

- When a part is marked as ``salvaged``, you can enter the old barcode data here.

Fields
------

Asset fields has been split into sections in forms:

- **Basic info**:
    - **Type** - a read only field for data center, back office or administration for back offic. Administration is used for assets like buildings etc.
    - **Model** - type a couple of letters to search for a given model. If no result is found, just click "Add" button to add it.
    - **Inventory number** -
    - **Warehouse** - the place where the asset is located.
    - **Location** - a more exact location of the device in the building/room.
    - **Status** - an asset's lifetime indicator. Newly bought assets has status "new". You can change it as required according to your own work flow.
    - **Task url** - url to task in ticket system
    - **Additional remarks** - additional info.
    - **Service name** - service name to which the asset belongs
    - **Property of** - to which the company belongs asset
- **Financial Info**:
    - **Price** - the unit price of the asset.
    - **Provider** - the name of the provider of the asset.
    - **Depreciation rate** - number of months this device deprecates
    - **Source** - if this device was purchased or salvaged
    - **Request date** - date of submission of the demand for the device.
    - **Delivery date** - date of device delivery.
    - **Deprecation end date** - the end day of the depreciation
    - **Order number**, **Invoice date**, **Invoice no**, **Provider order date**, **Budget info**.
- **User info**:
    - **User** - device user.
    - **Owner** - device owner.
- **Aditional info**:
    - **U level** - "U" level of installation device.
    - **U height** - how large the device is, in "U".
    - **Ralph device id** - ID device detected by Ralph Scan.


Bulk Editing
------------

It is often required to edit multiple assets at once. For example, when you
want to move them from one warehouse to another. There is a special mode called
"bulk edit" for this case.

To activate this mode, go to the search screen, and select multiple assets
using check marks on the left side.

.. image:: images/bulk-1.png

When ready, choose "Edit selected" from the bulk edit actions.

.. image:: images/bulk-2.png
    :scale: 55%

On the next screen you can edit those records all at once by changing the
appropriate fields. When you fill one field with the desired value, you can
propagate this value to all records by clicking on the "plus" mark near the
current cell.


Work Flow and Statues
---------------------

.. image:: images/edit-device-status.png


In this version there are no limits for moving assets from one status to
another.  You can freely change statuses.  All changes will be recorded,
allowing you to inspect the flow later.


Licences
^^^^^^^^
Ralph Assets allows you to store information about software licenses.
Adding and editing is performed in much the same way as in assets.

Adding License
--------------

To add a license, click the "Add support" option from the top of submenu.

.. image:: images/add_licence.png
    :scale: 75%


Fields
------

Licence fields are split into 2 section: **Basic info** and **Financial info**.
**Financial info** contains very important field, **Number of purchased items**.
This field ability to store Multi-Seat licence.


Relations
---------

Licenses may be related to the relationship with the user or device.
In asset and user form, during the search are shown only unassigned license,
that is, those that have still free slots.


Supports
^^^^^^^^

Ralph Assets allows you to store information about supports.
Adding and editing is performed in much the same way as in assets.

Adding Support
--------------

To add a support, click the "Add support" option from the top of submenu.

.. image:: images/add_support.png
    :scale: 75%

Relations
---------

Support can be assigned to a device. On the asset form page, there is the
option of marking device that requires a support.
This is valuable information that helps you better manage supports.


Users
^^^^^

User Page
---------

User page contains all information about user. User's devices, licenses,
personal information and transition history.

.. image:: images/user_page.png
    :scale: 75%


Admin
^^^^^

Administration interface is accessible from within the menu.

Here you can define

* models,
* categories,
* warehouses,
* other dictionary data.
