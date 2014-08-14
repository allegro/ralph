quicktest:
	DJANGO_SETTINGS_PROFILE=test-ralph ralph test ralph

flake:
	flake8 --exclude=migrations,tests,doc,www,settings.py --ignore=E501 src/ralph

runserver:
	ralph runserver
	
install:
	pip install -e . --use-mirrors --allow-all-external --allow-unverified ipaddr --allow-unverified postmarkup --allow-unverified python-graph-core --allow-unverified pysphere

test-unittests:
	DJANGO_SETTINGS_PROFILE=test-ralph coverage run --source=ralph --omit='*migrations*,*tests*' '$(VIRTUAL_ENV)/bin/ralph' test ralph

test-doc:
	ls -l src/ralph
	tree .
	# ignore warnings about missing subdirs - cloned from another repositories
	echo "test\n=====" > doc/optional_modules/assets/index.rst
	echo "test\n=====" > doc/optional_modules/pricing/index.rst
	cd doc && make html


test-with-coveralls: test-doc test-unittests
