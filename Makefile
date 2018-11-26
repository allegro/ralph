TEST?=ralph

.PHONY: test flake clean coverage docs coveralls

release-new-version: new_version = $(shell ./get_version.sh generate)
release-new-version:
	docker build -f docker_ng/Dockerfile-deb -t ralph-deb .
	docker run -it -v $(shell pwd):/volume ralph-deb:latest release-new-version
	docker image rm --force ralph-deb:latest
	git add debian/changelog
	git commit -m "Updated changelog for $(new_version) version."
	git tag -m $(new_version) -a $(new_version) -s

build-package:
	docker build -f docker_ng/Dockerfile-deb -t ralph-deb .
	docker run -it -v $(shell pwd):/volume ralph-deb:latest build-package
	docker image rm --force ralph-deb:latest

build-snapshot-package:
	docker build -f docker_ng/Dockerfile-deb -t ralph-deb .
	docker run -it -v $(shell pwd):/volume ralph-deb:latest build-snapshot-package
	docker image rm --force ralph-deb:latest

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
