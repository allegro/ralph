.. _history:

History module
=================
This module observe any changes on registered models and use Django's
signals to detect changes on model. Field excluded from history (on default):
	* ``created``,
	* ``modified``,
	* ``invoice_date``,
	* ``cache_version``,
	* ``rght``,
	* ``level``,
	* ``lft``,
	* ``tree_id``,

You can change this list by overriding ``exclude_fields_from_history()`` method
in model which is registered.

Features:
	* one history view for all models,
	* simple API,
	* stored information from all field types included ``ForeignKey`` and ``ManyToManyField``,
	* bulk create for many changes,
	* based on Django's content types.


Typical usage
~~~~~~~~~~~~~

Add ``HistoryMixin`` to model. That's all.


API
~~~

Add to history::

	from ralph_assets.history import History

	changes = [
		{
			'field_name': 'foo',
			'old_value': 123,
			'new_value': 321,
		},
		{
			'field_name': 'bar',
			'old_value': 'Lorem ips',
			'new_value': 'Lorem ipsum',
		},
	]
	History.objects.log_changes(asset, user, changes)


Get history for concrete object::

	from ralph_assets.history import History

	history = History.objects.get_history_for_this_object(asset)
