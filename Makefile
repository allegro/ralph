.PHONY: test flake clean coverage doc coveralls

test: clean
	ralph test --settings=ralph.settings.test

flake: clean
	flake8 --exclude=migrations,tests,doc,www,settings.py --ignore=E501 src/ralph

clean:
	find . -name '*.pyc' -exec rm -rf {} \;

coverage: clean
	coverage run --source=ralph --omit='*migrations*,*tests*,*__init__*,*wsgi.py,*__main__*,*settings*,*manage.py' '$(VIRTUAL_ENV)/bin/ralph' test ralph --settings=ralph.settings.test

doc:
	mkdir -p www/_build/html/ 2>/dev/null
	cd ./doc && make html

coveralls: doc test
