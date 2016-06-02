TEST?=ralph

.PHONY: test flake clean coverage docs coveralls

package: build-package upload-package

build-package:
	rm -rf ./build 2>/dev/null 1>/dev/null
	./packaging/build-package.sh

upload-package:
	./packaging/upload-package.sh

install-js:
	npm install
	bower install

js-hint:
	find src/ralph|grep "\.js$$"|grep -v vendor|xargs ./node_modules/.bin/jshint;

install: install-js
	pip3 install -r requirements/prod.txt

install-test:
	pip3 install -r requirements/test.txt

install-dev:
	pip3 install -r requirements/dev.txt

install-docs:
	pip3 install -r requirements/docs.txt

isort:
	isort --diff --recursive --check-only --quiet src

test: clean
	test_ralph test $(TEST)

flake: isort
	flake8 src/ralph
	@cat scripts/flake.txt

clean:
	find . -name '*.py[cod]' -exec rm -rf {} \;

coverage: clean
	coverage run $(shell which test_ralph) test $(TEST) --settings="ralph.settings.test"
	coverage report

docs:
	mkdocs build

run:
	dev_ralph runserver_plus 0.0.0.0:8000

menu:
	ralph sitetree_resync_apps

coveralls: install-docs docs coverage

translate_messages:
	ralph makemessages -a

compile_messages:
	ralph compilemessages
