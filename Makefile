.PHONY: test flake clean coverage docs coveralls

install:
	pip install -e .

install-test:
	pip install -r requirements/test.txt

install-dev:
	pip install -r requirements/dev.txt

test: clean
	test_ralph test ralph

flake: clean
	flake8 src/ralph

clean:
	find . -name '*.py[cod]' -exec rm -rf {} \;

coverage: clean
	coverage run '$(VIRTUAL_ENV)/bin/test_ralph' test ralph

docs:
	cd ./docs && make html

coveralls: docs coverage
