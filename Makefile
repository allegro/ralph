quicktest:
	DJANGO_SETTINGS_PROFILE=test-ralph ralph test ralph

flake:
	flake8 --exclude=migrations,tests,doc,www,settings.py --ignore=E501,E731,W503 src/ralph

runserver:
	ralph runserver

collectstatic:
	ralph collectstatic --noinput

install:
	pip install -e . --allow-all-external --allow-unverified ipaddr --allow-unverified postmarkup --allow-unverified pysphere --find-links=https://pypi.python.org/pypi/pysphere/0.1.8

test-unittests:
	DJANGO_SETTINGS_PROFILE=test-ralph coverage run --source=ralph --omit='*migrations*,*tests*,*__init__*,*wsgi.py,*__main__*,*settings*,*manage.py,src/ralph/util/demo/*' '$(VIRTUAL_ENV)/bin/ralph' test ralph

test-doc:
	# ignore warnings about missing subdirs - cloned from another repositories
	mkdir  ./doc/optional_modules/assets/ 2>/dev/null; exit 0
	mkdir  ./doc/optional_modules/pricing/ 2>/dev/null; exit 0
	mkdir -p www/_build/html/ 2>/dev/null
	echo "test\n=====" > ./doc/optional_modules/assets/index.rst
	echo "test\n=====" > ./doc/optional_modules/pricing/index.rst
	cd ./doc && make html


test-with-coveralls: test-doc test-unittests
check-templates:
	django-template-i18n-lint .
