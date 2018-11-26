TEST?=ralph

.PHONY: test flake clean coverage docs coveralls

package: build-package upload-package

build-package-docker:
	rm -rf ./build 2>/dev/null 1>/dev/null
	./packaging/build-package-ng.sh
	mkdir -p /volume/build
	cp ../*.deb /volume/build
	cp debian/changelog /volume/debian/changelog

build-package:
	docker build -f docker_ng/Dockerfile-deb -t ralph-deb .
	docker run -i -v $(shell pwd):/volume ralph-deb:latest
	docker image rm --force ralph-deb:latest

upload-package:
	./packaging/upload-package.sh

build-docker:
	docker build -f docker_ng/Dockerfile-prod -t allegro/ralphng:$(shell ./get_version.sh) ./docker_ng/

install-js:
	npm install
	bower install
	./node_modules/.bin/gulp

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
	flake8 src/ralph/settings --ignore=F405 --exclude=*local.py
	@cat scripts/flake.txt

clean:
	find . -name '*.py[cod]' -exec rm -rf {} \;

coverage: clean
	coverage run $(shell which test_ralph) test $(TEST) --keepdb --settings="ralph.settings.test"
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
