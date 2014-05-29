quicktest:
	DJANGO_SETTINGS_PROFILE=test-ralph ralph test ralph

flake:
	flake8 --exclude=migrations,tests,doc,www,settings.py --ignore=E501 src/ralph

runserver:
	ralph runserver
	
install:
	pip install -e . --use-mirrors --allow-all-external --allow-unverified ipaddr --allow-unverified postmarkup --allow-unverified python-graph-core --allow-unverified pysphere

test-with-coveralls:
	DJANGO_SETTINGS_PROFILE=test-ralph coverage run --source=ralph --omit='*migrations*,*tests*' '$(VIRTUAL_ENV)/bin/ralph' test ralph
