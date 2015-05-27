TEST?=ralph

.PHONY: test flake clean coverage docs coveralls

fix_tablib:
	# https://github.com/kennethreitz/tablib/issues/177
	pip install 'git+https://github.com/kennethreitz/tablib.git@develop'

install: fix_tablib
	pip install -e .

install-test: fix_tablib
	pip install -r requirements/test.txt

install-dev: fix_tablib
	pip install -r requirements/dev.txt

test: clean
	test_ralph test $(TEST)

flake: clean
	flake8 src/ralph

clean:
	find . -name '*.py[cod]' -exec rm -rf {} \;

coverage: clean
	coverage run '$(VIRTUAL_ENV)/bin/test_ralph' test ralph
	coverage report

docs:
	cd ./docs && make html

coveralls: docs coverage
